#!/usr/bin/env python3
import os
import sys
import shutil
import subprocess
from pathlib import Path
import questionary


def run(cmd, cwd=None, env=None):
    print("▶", " ".join(cmd))
    subprocess.check_call(cmd, cwd=cwd, env=env)


def capture(cmd, cwd=None, env=None) -> str:
    return subprocess.check_output(cmd, cwd=cwd, env=env, text=True).strip()


def need(cmd_name: str) -> bool:
    return shutil.which(cmd_name) is not None


def die(msg: str):
    print(f"❌ {msg}", file=sys.stderr)
    sys.exit(1)


def info(msg: str):
    print(f"ℹ️  {msg}")


def ok(msg: str):
    print(f"✅ {msg}")


def tf_output(env, cwd: str, name: str) -> str | None:
    """Return terraform output -raw <name> or None if not found."""
    try:
        return capture(["terraform", "output", "-raw", name], cwd=cwd, env=env)
    except subprocess.CalledProcessError:
        return None


def write_backend_hcl_with_meta(path: Path, bucket: str, key: str, region: str, test_via_ui: bool) -> None:
    """
    Write Terraform backend config (valid HCL) plus metadata as comment.
    Terraform ignores comments; a destroy script can read meta.test_via_ui from the first line.
    """
    meta_line = f"# meta.test_via_ui={'true' if test_via_ui else 'false'}\n"
    content = (
        meta_line
        + f'bucket  = "{bucket}"\n'
        f'key     = "{key}"\n'
        f'region  = "{region}"\n'
        f'encrypt = true\n'
    )
    path.write_text(content, encoding="utf-8")


def main():
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent

    ROOT = project_root / "cloud_infrastructure" / "infrastructure"
    BOOT = ROOT / "bootstrap"

    if not ROOT.exists():
        die(f"Terraform root not found: {ROOT}")
    if not BOOT.exists():
        die(f"Bootstrap dir not found: {BOOT}")

    env = os.environ.copy()

    # Step 1: tool checks
    info("Checking required tools...")
    if not need("aws"):
        die("Missing aws CLI. Install: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html")
    if not need("terraform"):
        die("Missing terraform. Install: https://developer.hashicorp.com/terraform/install")

    ok(capture(["aws", "--version"]))
    ok(capture(["terraform", "version"]).splitlines()[0])

    # Step 2: AWS profile selection
    profiles_raw = capture(["aws", "configure", "list-profiles"])
    profiles = [p for p in profiles_raw.splitlines() if p]
    if not profiles:
        die("No AWS profiles found. Run: aws configure --profile <name>")

    aws_profile = questionary.select(
        "Select AWS profile:",
        choices=profiles,
    ).ask()
    if not aws_profile:
        die("AWS profile selection cancelled.")

    env["AWS_PROFILE"] = aws_profile
    ok(f"Using AWS_PROFILE={aws_profile}")

    # Step 3: Release UI?
    release_ui = questionary.confirm(
        "Release UI site as well?",
        default=False,
    ).ask()
    ok(f"RELEASE_UI={release_ui}")

    # Step 4: Region
    region = questionary.text(
        "AWS region:",
        default="eu-central-1",
    ).ask()
    if not region:
        die("Region required.")

    # Step 5: State key
    key = questionary.text(
        "Terraform state key:",
        default="terraform.tfstate",
    ).ask()
    if not key:
        die("State key required.")

    ok(f"REGION={region}, KEY={key}")

    # Step 6: Bootstrap backend (S3 bucket)
    info("Bootstrapping backend...")
    run(["terraform", "init"], cwd=str(BOOT), env=env)

    boot_vars = [
        f"region={region}",
        f"profile={aws_profile}",
    ]
    run(
        ["terraform", "apply", "-auto-approve"] + [f"-var={v}" for v in boot_vars],
        cwd=str(BOOT),
        env=env,
    )

    # read bucket output (support both output names)
    bucket = tf_output(env, str(BOOT), "backend_s3_bucket_name")
    if not bucket:
        bucket = tf_output(env, str(BOOT), "backend_s3_bucket_arn")
    if not bucket:
        die("Bootstrap output bucket name not found (expected backend_s3_bucket_name or backend_s3_bucket_arn).")

    ok(f"State bucket: {bucket}")

    # write backend.hcl (NO dynamodb lock) + meta.test_via_ui for destroy script
    backend_hcl = ROOT / "backend.hcl"
    info(f"Writing {backend_hcl} (with meta.test_via_ui)")
    write_backend_hcl_with_meta(
        path=backend_hcl,
        bucket=bucket,
        key=key,
        region=region,
        test_via_ui=bool(release_ui),
    )
    ok("backend.hcl ready")

    # Step 7: Init+Migrate root (requires terraform { backend "s3" {} } in ROOT/backend.tf)
    info("Initializing root infrastructure (S3 backend)...")
    init_cmd_migrate = ["terraform", "init", "-migrate-state", f"-backend-config={backend_hcl.name}"]
    init_cmd_reconfig = ["terraform", "init", "-reconfigure", f"-backend-config={backend_hcl.name}"]

    try:
        run(init_cmd_migrate, cwd=str(ROOT), env=env)
    except subprocess.CalledProcessError:
        info("Init migrate failed (likely already migrated). Reconfiguring backend...")
        run(init_cmd_reconfig, cwd=str(ROOT), env=env)

    tf_vars = [
        f"region={region}",
        f"profile={aws_profile}",
        f"test_via_ui={'true' if release_ui else 'false'}",
    ]

    run(
        ["terraform", "apply", "-auto-approve"] + [f"-var={v}" for v in tf_vars],
        cwd=str(ROOT),
        env=env,
    )
    ok("Infrastructure deployed")

    print("\nTerraform outputs:")
    try:
        print(capture(["terraform", "output"], cwd=str(ROOT), env=env))
    except subprocess.CalledProcessError:
        pass

    api_base_url = tf_output(env, str(ROOT), "api_base_url")
    if not api_base_url:
        die("Missing output 'api_base_url' in root. Expose it from your Terraform outputs.")
    ok(f"API Base URL: {api_base_url}")

    frontend_env = ROOT / "s3_website" / "code" / ".env.local"
    frontend_env.parent.mkdir(parents=True, exist_ok=True)
    frontend_env.write_text(f"VITE_API_BASE_URL={api_base_url}\n", encoding="utf-8")
    ok(f"Created {frontend_env}")

    # Step 8: UI deploy
    if release_ui:
        if not need("npm"):
            die("Missing npm/node. Install Node.js: https://nodejs.org/")

        website_bucket = tf_output(env, str(ROOT), "website_bucket_name")
        website_url = tf_output(env, str(ROOT), "website_url")

        if not website_bucket:
            die("Missing output 'website_bucket_name'. Ensure it exists when test_via_ui=true.")

        ok(f"Website bucket: {website_bucket}")
        if website_url:
            ok(f"Website URL: {website_url}")

        frontend_dir = ROOT / "s3_website" / "code"
        dist_dir = frontend_dir / "dist"

        info("Building frontend...")
        # npm ci requires package-lock.json; fallback to npm install if missing
        pkg_lock = frontend_dir / "package-lock.json"
        if pkg_lock.exists():
            run(["npm", "ci"], cwd=str(frontend_dir), env=env)
        else:
            info("package-lock.json not found -> using npm install")
            run(["npm", "install"], cwd=str(frontend_dir), env=env)

        run(["npm", "run", "build"], cwd=str(frontend_dir), env=env)

        if not dist_dir.exists():
            die(f"Build output not found: {dist_dir} (if not Vite, adjust dist/build)")

        info("Uploading to S3...")
        run(
            ["aws", "s3", "sync", str(dist_dir), f"s3://{website_bucket}/", "--delete"],
            cwd=str(project_root),
            env=env,
        )

        ok("Upload completed")
        if website_url:
            print("\n🌐 URL:", website_url)

    ok("All done.")


if __name__ == "__main__":
    main()