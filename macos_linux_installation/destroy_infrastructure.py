#!/usr/bin/env python3
"""
Destroy script for Mac/Linux.

Sequence:
1) If meta.test_via_ui=true and website bucket output exists -> empty S3 website bucket
2) terraform destroy ROOT (main infrastructure)
3) Empty Terraform backend state bucket (from bootstrap output)
4) terraform destroy BOOTSTRAP

Reads meta.test_via_ui from ROOT/backend.hcl (comment line written by first_configuration.py).
Does not fail if website_bucket_name output is missing (e.g. UI was never deployed).
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import questionary


def die(msg: str, code: int = 1) -> None:
    print(f"❌ {msg}", file=sys.stderr)
    sys.exit(code)


def info(msg: str) -> None:
    print(f"ℹ️  {msg}")


def ok(msg: str) -> None:
    print(f"✅ {msg}")


def warn(msg: str) -> None:
    print(f"⚠️  {msg}")


def run(cmd: list[str], cwd: str | None = None, env: dict | None = None) -> None:
    print("▶", " ".join(cmd), f"(cwd={cwd})" if cwd else "")
    subprocess.check_call(cmd, cwd=cwd, env=env)


def capture(cmd: list[str], cwd: str | None = None, env: dict | None = None) -> str:
    return subprocess.check_output(cmd, cwd=cwd, env=env, text=True, encoding="utf-8", errors="replace").strip()


def capture_soft(cmd: list[str], cwd: str | None = None, env: dict | None = None) -> str | None:
    """Run command; return output or None on non-zero exit (for optional terraform outputs)."""
    try:
        return subprocess.check_output(
            cmd, cwd=cwd, env=env, text=True, encoding="utf-8", errors="replace"
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def capture_json(cmd: list[str], cwd: str | None = None, env: dict | None = None) -> Any:
    out = capture(cmd, cwd=cwd, env=env)
    if not out:
        return None
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        die(f"Expected JSON output but got:\n{out}")


def need(cmd_name: str) -> bool:
    return shutil.which(cmd_name) is not None


# ---------------------------
# Terraform
# ---------------------------


def tf_output_soft(env: dict, cwd: str, name: str) -> str | None:
    """terraform output -raw <name>; returns None if output missing or command fails."""
    return capture_soft(["terraform", "output", "-raw", name], cwd=cwd, env=env)


def parse_bucket_name(value: str) -> str:
    v = value.strip()
    if v.startswith("arn:aws:s3:::"):
        return v.split("arn:aws:s3:::")[-1].strip("/")
    return v


# ---------------------------
# backend.hcl meta
# ---------------------------


def read_backend_meta_test_via_ui(backend_hcl: Path) -> bool | None:
    """
    Read '# meta.test_via_ui=true/false' from backend.hcl.
    Returns True/False if found, else None.
    """
    if not backend_hcl.exists():
        return None
    try:
        for line in backend_hcl.read_text(encoding="utf-8").splitlines():
            s = line.strip().lower()
            if s.startswith("#") and "meta.test_via_ui=" in s:
                val = s.split("meta.test_via_ui=", 1)[-1].strip()
                if val in ("true", "false"):
                    return val == "true"
    except Exception:
        return None
    return None


# ---------------------------
# S3 empty (handles versioning)
# ---------------------------


def s3_bucket_exists(env: dict, bucket: str) -> bool:
    try:
        subprocess.check_call(
            ["aws", "s3api", "head-bucket", "--bucket", bucket],
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except Exception:
        return False


def s3_empty_bucket(env: dict, bucket: str) -> None:
    if not bucket:
        return
    bucket = parse_bucket_name(bucket)
    if not s3_bucket_exists(env, bucket):
        warn(f"Bucket not found or not accessible: {bucket} (skipping empty)")
        return

    info(f"Emptying S3 bucket: {bucket}")

    try:
        run(["aws", "s3", "rm", f"s3://{bucket}", "--recursive"], env=env)
    except subprocess.CalledProcessError:
        warn("aws s3 rm failed; continuing with versioned deletion...")

    key_markers: dict[str, str | None] = {"KeyMarker": None, "VersionIdMarker": None}

    while True:
        cmd = [
            "aws", "s3api", "list-object-versions",
            "--bucket", bucket,
            "--output", "json",
        ]
        if key_markers["KeyMarker"]:
            cmd += ["--key-marker", key_markers["KeyMarker"]]
        if key_markers["VersionIdMarker"]:
            cmd += ["--version-id-marker", key_markers["VersionIdMarker"]]

        data = capture_json(cmd, env=env) or {}
        versions = data.get("Versions", []) or []
        markers = data.get("DeleteMarkers", []) or []

        to_delete: list[dict[str, str]] = []
        for v in versions:
            k, vid = v.get("Key"), v.get("VersionId")
            if k and vid:
                to_delete.append({"Key": k, "VersionId": vid})
        for m in markers:
            k, vid = m.get("Key"), m.get("VersionId")
            if k and vid:
                to_delete.append({"Key": k, "VersionId": vid})

        for i in range(0, len(to_delete), 1000):
            chunk = to_delete[i : i + 1000]
            payload = {"Objects": chunk, "Quiet": True}
            run(
                [
                    "aws", "s3api", "delete-objects",
                    "--bucket", bucket,
                    "--delete", json.dumps(payload),
                ],
                env=env,
            )

        if not data.get("IsTruncated"):
            break
        key_markers["KeyMarker"] = data.get("NextKeyMarker")
        key_markers["VersionIdMarker"] = data.get("NextVersionIdMarker")
        if not key_markers["KeyMarker"] and not key_markers["VersionIdMarker"]:
            warn("Pagination markers missing while IsTruncated=true. Stopping.")
            break

    ok(f"Bucket emptied: {bucket}")


# ---------------------------
# Main
# ---------------------------


def main() -> None:
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent

    ROOT = project_root / "cloud_infrastructure" / "infrastructure"
    BOOT = ROOT / "bootstrap"

    if not ROOT.exists():
        die(f"Terraform root not found: {ROOT}")
    if not BOOT.exists():
        die(f"Bootstrap dir not found: {BOOT}")

    env = os.environ.copy()

    info("Checking required tools...")
    if not need("aws"):
        die("Missing aws CLI. Install: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html")
    if not need("terraform"):
        die("Missing terraform. Install: https://developer.hashicorp.com/terraform/install")

    ok(capture(["aws", "--version"], env=env))
    ok(capture(["terraform", "version"], env=env).splitlines()[0])

    profiles_raw = capture(["aws", "configure", "list-profiles"], env=env)
    profiles = [p.strip() for p in profiles_raw.splitlines() if p.strip()]
    if not profiles:
        die("No AWS profiles found. Run: aws configure --profile <name>")

    aws_profile = questionary.select("Select AWS profile:", choices=profiles).ask()
    if not aws_profile:
        die("AWS profile selection cancelled.")

    env["AWS_PROFILE"] = aws_profile
    ok(f"Using AWS_PROFILE={aws_profile}")

    region = questionary.text("AWS region:", default="eu-central-1").ask()
    if not region:
        die("Region required.")
    env.setdefault("AWS_REGION", region)
    env.setdefault("AWS_DEFAULT_REGION", region)
    ok(f"REGION={region}")

    confirm = questionary.confirm(
        "This will DESTROY the entire infrastructure and delete S3 content. Continue?",
        default=False,
    ).ask()
    if not confirm:
        die("Cancelled by user.", code=0)

    backend_hcl = ROOT / "backend.hcl"
    if not backend_hcl.exists():
        warn(f"{backend_hcl} not found. Terraform init may fail if backend isn't configured.")
        warn("If needed, run first_configuration.py once to generate it.")

    meta_test_via_ui = read_backend_meta_test_via_ui(backend_hcl)
    if meta_test_via_ui is None:
        warn("meta.test_via_ui not found in backend.hcl -> assuming UI was NOT deployed.")
        meta_test_via_ui = False
    ok(f"meta.test_via_ui={meta_test_via_ui}")

    info("Initializing ROOT terraform (best effort)...")
    init_cmd = ["terraform", "init"]
    if backend_hcl.exists():
        init_cmd = ["terraform", "init", "-reconfigure", f"-backend-config={backend_hcl.name}"]
    try:
        subprocess.check_call(init_cmd, cwd=str(ROOT), env=env)
    except subprocess.CalledProcessError as e:
        warn(f"ROOT terraform init failed (continuing): {e}")

    website_bucket = ""
    if meta_test_via_ui:
        website_bucket = tf_output_soft(env, str(ROOT), "website_bucket_name") or ""
        if not website_bucket:
            warn("website_bucket_name output not found -> skipping s3_website empty.")

    # Step 1: empty website bucket
    if website_bucket:
        info("Step 1/4: Empty website bucket (s3_website)")
        s3_empty_bucket(env, website_bucket)
    else:
        info("Step 1/4: No website bucket to empty (skipped)")

    # Step 2: destroy ROOT
    tf_vars = [f"profile={aws_profile}", f"region={region}"]
    info("Step 2/4: Destroy ROOT infrastructure")
    run(
        ["terraform", "destroy", "-auto-approve"] + [f"-var={v}" for v in tf_vars],
        cwd=str(ROOT),
        env=env,
    )
    ok("ROOT infrastructure destroyed")

    info("Initializing BOOTSTRAP terraform (for backend bucket output)...")
    try:
        subprocess.check_call(["terraform", "init"], cwd=str(BOOT), env=env)
    except subprocess.CalledProcessError as e:
        warn(f"BOOT terraform init failed (continuing): {e}")

    backend_bucket = (
        tf_output_soft(env, str(BOOT), "backend_s3_bucket_name")
        or tf_output_soft(env, str(BOOT), "backend_s3_bucket_arn")
        or ""
    )

    # Step 3: empty state bucket
    info("Step 3/4: Empty terraform state bucket")
    if backend_bucket:
        s3_empty_bucket(env, backend_bucket)
    else:
        warn("Bootstrap backend bucket output not found (skipping state bucket empty).")

    # Step 4: destroy BOOT
    info("Step 4/4: Destroy BOOTSTRAP infrastructure")
    run(
        ["terraform", "destroy", "-auto-approve"] + [f"-var={v}" for v in tf_vars],
        cwd=str(BOOT),
        env=env,
    )
    ok("BOOTSTRAP infrastructure destroyed")

    ok("All done. Infrastructure removed.")


if __name__ == "__main__":
    main()
