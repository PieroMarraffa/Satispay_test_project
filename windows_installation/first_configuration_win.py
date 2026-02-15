#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Windows-hardened provisioning script.

Goals:
- Be resilient to PATH / PATHEXT differences across Windows machines and IDE runners
- Resolve executables robustly (aws, terraform, npm)
- Provide clear diagnostics when something is missing or fails
- Keep behavior compatible with your original script

Fix:
- Write metadata in backend.hcl as comment: # meta.test_via_ui=true/false
  (Terraform backend config cannot accept arbitrary keys, so we store it as a comment)
"""

from __future__ import annotations

import os
import sys
import shutil
import subprocess
from pathlib import Path

import questionary


# ---------------------------
# Console helpers
# ---------------------------

def die(msg: str, code: int = 1):
    print(f"❌ {msg}", file=sys.stderr)
    sys.exit(code)


def info(msg: str):
    print(f"ℹ️  {msg}")


def ok(msg: str):
    print(f"✅ {msg}")


def warn(msg: str):
    print(f"⚠️  {msg}")


# ---------------------------
# Environment & executable resolution (Windows-hardened)
# ---------------------------

def ensure_windows_env_basics(env: dict) -> dict:
    env = dict(env)

    env.setdefault("PATHEXT", os.environ.get("PATHEXT", ".COM;.EXE;.BAT;.CMD;.VBS;.VBE;.JS;.JSE;.WSF;.WSH;.MSC"))

    user_profile = env.get("USERPROFILE") or os.environ.get("USERPROFILE")
    if user_profile:
        npm_shim = str(Path(user_profile) / "AppData" / "Roaming" / "npm")
        if os.path.isdir(npm_shim):
            path_val = env.get("PATH", "")
            paths = [p for p in path_val.split(os.pathsep) if p]
            lower = {p.lower() for p in paths}
            if npm_shim.lower() not in lower:
                env["PATH"] = npm_shim + os.pathsep + path_val

    return env


def which_any(names: list[str], env: dict | None = None) -> str | None:
    for n in names:
        p = shutil.which(n, path=(env.get("PATH") if env else None))
        if p:
            return p
    return None


def require_exe(tool: str, env: dict, extra_names: list[str] | None = None, install_hint: str | None = None) -> str:
    candidates = [tool]
    if os.name == "nt":
        candidates += [f"{tool}.exe", f"{tool}.cmd", f"{tool}.bat"]
    if extra_names:
        candidates += extra_names

    found = which_any(candidates, env=env) or which_any(candidates, env=None)
    if not found:
        hint = f"\nInstall: {install_hint}" if install_hint else ""
        debug = (
            f"Tool '{tool}' not found in PATH for this Python process.\n"
            f"Python: {sys.executable}\n"
            f"PATH (first 400 chars): {env.get('PATH','')[:400]}...\n"
            f"PATHEXT: {env.get('PATHEXT','')}\n"
        )
        die(debug + hint)
    return found


# ---------------------------
# Subprocess helpers
# ---------------------------

def fmt_cmd(cmd: list[str]) -> str:
    def q(s: str) -> str:
        return f'"{s}"' if (" " in s or "\t" in s) else s
    return " ".join(q(x) for x in cmd)


def run(cmd: list[str], cwd: str | None = None, env: dict | None = None):
    print("▶", fmt_cmd(cmd), f"(cwd={cwd})" if cwd else "")
    try:
        subprocess.check_call(cmd, cwd=cwd, env=env)
    except FileNotFoundError as e:
        die(
            f"Command not found: {cmd[0]}\n"
            f"cwd: {cwd}\n"
            f"Details: {e}\n"
            f"TIP: This usually means PATH/PATHEXT differs in the runner (IDE vs terminal)."
        )
    except subprocess.CalledProcessError as e:
        die(f"Command failed (exit {e.returncode}): {fmt_cmd(cmd)}\n" f"cwd: {cwd}")


def capture(cmd: list[str], cwd: str | None = None, env: dict | None = None) -> str:
    try:
        return subprocess.check_output(cmd, cwd=cwd, env=env, text=True).strip()
    except FileNotFoundError as e:
        die(f"Command not found: {cmd[0]}\n" f"cwd: {cwd}\n" f"Details: {e}")
    except subprocess.CalledProcessError as e:
        die(f"Command failed (exit {e.returncode}): {fmt_cmd(cmd)}\n" f"cwd: {cwd}")
    return ""


def tf_output(terraform_exe: str, env: dict, cwd: str, name: str) -> str | None:
    try:
        return capture([terraform_exe, "output", "-raw", name], cwd=cwd, env=env)
    except SystemExit:
        raise
    except Exception:
        return None


# ---------------------------
# Backend meta helpers
# ---------------------------

def write_backend_hcl_with_meta(path: Path, bucket: str, key: str, region: str, test_via_ui: bool):
    """
    Writes Terraform backend config (valid HCL) + metadata as comment.
    Terraform ignores comments; our destroy script can read them.
    """
    meta_line = f"# meta.test_via_ui={'true' if test_via_ui else 'false'}\n"
    content = (
        meta_line +
        f'bucket  = "{bucket}"\n'
        f'key     = "{key}"\n'
        f'region  = "{region}"\n'
        f'encrypt = true\n'
    )
    path.write_text(content, encoding="utf-8")


# ---------------------------
# Main
# ---------------------------

def main():
    if os.name != "nt":
        warn("This script is optimized for Windows; it may still work on other OSes, but is not guaranteed.")

    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent

    ROOT = project_root / "cloud_infrastructure" / "infrastructure"
    BOOT = ROOT / "bootstrap"

    if not ROOT.exists():
        die(f"Terraform root not found: {ROOT}")
    if not BOOT.exists():
        die(f"Bootstrap dir not found: {BOOT}")

    env = ensure_windows_env_basics(os.environ.copy())

    info("Checking required tools...")
    aws_exe = require_exe("aws", env=env, install_hint="https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html")
    terraform_exe = require_exe("terraform", env=env, install_hint="https://developer.hashicorp.com/terraform/install")

    ok(capture([aws_exe, "--version"], env=env))
    ok(capture([terraform_exe, "version"], env=env).splitlines()[0])

    profiles_raw = capture([aws_exe, "configure", "list-profiles"], env=env)
    profiles = [p.strip() for p in profiles_raw.splitlines() if p.strip()]
    if not profiles:
        die("No AWS profiles found. Run: aws configure --profile <name>")

    aws_profile = questionary.select("Select AWS profile:", choices=profiles).ask()
    if not aws_profile:
        die("AWS profile selection cancelled.")

    env["AWS_PROFILE"] = aws_profile
    env["AWS_SDK_LOAD_CONFIG"] = "1"
    env["TF_VAR_profile"] = aws_profile
    ok(f"Using AWS_PROFILE={aws_profile}")

    release_ui = questionary.confirm("Release UI site as well?", default=False).ask()
    ok(f"RELEASE_UI={release_ui}")

    region = questionary.text("AWS region:", default="eu-central-1").ask()
    if not region:
        die("Region required.")
    env["AWS_REGION"] = region
    env["AWS_DEFAULT_REGION"] = region
    env["TF_VAR_region"] = region

    key = questionary.text("Terraform state key:", default="terraform.tfstate").ask()
    if not key:
        die("State key required.")

    ok(f"REGION={region}, KEY={key}")

    info("Bootstrapping backend...")
    run([terraform_exe, "init"], cwd=str(BOOT), env=env)

    boot_vars = [f"region={region}", f"profile={aws_profile}"]
    run([terraform_exe, "apply", "-auto-approve"] + [f"-var={v}" for v in boot_vars], cwd=str(BOOT), env=env)

    bucket = tf_output(terraform_exe, env, str(BOOT), "backend_s3_bucket_name")
    if not bucket:
        bucket = tf_output(terraform_exe, env, str(BOOT), "backend_s3_bucket_arn")
    if not bucket:
        die("Bootstrap output bucket name not found (expected backend_s3_bucket_name or backend_s3_bucket_arn).")

    ok(f"State bucket: {bucket}")

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

    info("Initializing root infrastructure (S3 backend)...")
    init_cmd_migrate = [terraform_exe, "init", "-migrate-state", f"-backend-config={backend_hcl.name}"]
    init_cmd_reconfig = [terraform_exe, "init", "-reconfigure", f"-backend-config={backend_hcl.name}"]

    # softer migrate flow
    print("▶", fmt_cmd(init_cmd_migrate), f"(cwd={ROOT})")
    migrate_ok = True
    try:
        subprocess.check_call(init_cmd_migrate, cwd=str(ROOT), env=env)
    except subprocess.CalledProcessError:
        migrate_ok = False
    except FileNotFoundError as e:
        die(f"terraform not runnable: {e}")

    if not migrate_ok:
        info("Init migrate failed (likely already migrated). Reconfiguring backend...")
        run(init_cmd_reconfig, cwd=str(ROOT), env=env)

    tf_vars = [
        f"region={region}",
        f"profile={aws_profile}",
        f"test_via_ui={'true' if release_ui else 'false'}",
    ]
    env["TF_VAR_test_via_ui"] = "true" if release_ui else "false"

    run([terraform_exe, "apply", "-auto-approve"] + [f"-var={v}" for v in tf_vars], cwd=str(ROOT), env=env)
    ok("Infrastructure deployed")

    print("\nTerraform outputs:")
    try:
        print(capture([terraform_exe, "output"], cwd=str(ROOT), env=env))
    except SystemExit:
        pass

    api_base_url = tf_output(terraform_exe, env, str(ROOT), "api_base_url")
    if not api_base_url:
        die("Missing output 'api_base_url' in root. Expose it from your Terraform outputs.")
    ok(f"API Base URL: {api_base_url}")

    frontend_env = ROOT / "s3_website" / "code" / ".env.local"
    frontend_env.parent.mkdir(parents=True, exist_ok=True)
    frontend_env.write_text(f"VITE_API_BASE_URL={api_base_url}\n", encoding="utf-8")
    ok(f"Created {frontend_env}")

    if release_ui:
        npm_exe = require_exe("npm", env=env, extra_names=["npm.cmd"], install_hint="https://nodejs.org/")
        node_exe = require_exe("node", env=env, extra_names=["node.exe"], install_hint="https://nodejs.org/")

        ok(f"node: {capture([node_exe, "-v"], env=env)}")
        ok(f"npm: {capture([npm_exe, "-v"], env=env)}")

        website_bucket = tf_output(terraform_exe, env, str(ROOT), "website_bucket_name")
        website_url = tf_output(terraform_exe, env, str(ROOT), "website_url")

        if not website_bucket:
            die("Missing output 'website_bucket_name'. Ensure it exists when test_via_ui=true.")

        ok(f"Website bucket: {website_bucket}")
        if website_url:
            ok(f"Website URL: {website_url}")

        frontend_dir = ROOT / "s3_website" / "code"
        dist_dir = frontend_dir / "dist"
        frontend_dir_abs = str(frontend_dir.resolve())

        info("Building frontend...")
        pkg_lock = frontend_dir / "package-lock.json"
        if pkg_lock.exists():
            run([npm_exe, "ci"], cwd=frontend_dir_abs, env=env)
        else:
            info("package-lock.json not found -> using npm install")
            run([npm_exe, "install"], cwd=frontend_dir_abs, env=env)

        run([npm_exe, "run", "build"], cwd=frontend_dir_abs, env=env)

        if not dist_dir.exists():
            alt_build = frontend_dir / "build"
            if alt_build.exists():
                warn(f"dist/ not found, but build/ exists. Using: {alt_build}")
                dist_dir = alt_build
            else:
                die(f"Build output not found: {dist_dir} (if not Vite, adjust dist/build)")

        info("Uploading to S3...")
        run([aws_exe, "s3", "sync", str(dist_dir), f"s3://{website_bucket}/", "--delete"], cwd=str(project_root), env=env)

        ok("Upload completed")
        if website_url:
            print("\n🌐 URL:", website_url)

    ok("All done.")


if __name__ == "__main__":
    main()
