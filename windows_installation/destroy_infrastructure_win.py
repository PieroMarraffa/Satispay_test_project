#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Windows-hardened destroy script.

Sequence:
1) If meta.test_via_ui=true and website bucket output exists -> empty s3_website bucket
2) terraform destroy ROOT (state must still exist)
3) empty terraform backend state bucket (backend_s3_bucket_name or backend_s3_bucket_arn)
4) terraform destroy BOOTSTRAP

Fixes:
- Read meta.test_via_ui from ROOT/backend.hcl comment
- Do NOT fail if terraform output website_bucket_name is missing (site not deployed)
"""

from __future__ import annotations

import os
import sys
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

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
    env.setdefault(
        "PATHEXT",
        os.environ.get("PATHEXT", ".COM;.EXE;.BAT;.CMD;.VBS;.VBE;.JS;.JSE;.WSF;.WSH;.MSC"),
    )

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


def capture_soft(cmd: list[str], cwd: str | None = None, env: dict | None = None) -> str | None:
    """
    Like capture(), but returns None on non-zero exit (doesn't kill the script).
    Useful for optional terraform outputs.
    """
    try:
        return subprocess.check_output(cmd, cwd=cwd, env=env, text=True).strip()
    except subprocess.CalledProcessError:
        return None
    except FileNotFoundError as e:
        die(f"Command not found: {cmd[0]}\n" f"cwd: {cwd}\n" f"Details: {e}")
    except Exception:
        return None


def capture_json(cmd: list[str], cwd: str | None = None, env: dict | None = None) -> Any:
    out = capture(cmd, cwd=cwd, env=env)
    if not out:
        return None
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        die(f"Expected JSON output but got:\n{out}")


# ---------------------------
# Terraform helpers
# ---------------------------

def tf_output_soft(terraform_exe: str, env: dict, cwd: str, name: str) -> str | None:
    """
    terraform output -raw <name> but returns None if output doesn't exist.
    """
    return capture_soft([terraform_exe, "output", "-raw", name], cwd=cwd, env=env)


def parse_bucket_name(value: str) -> str:
    v = value.strip()
    if v.startswith("arn:aws:s3:::"):
        return v.split("arn:aws:s3:::")[-1].strip("/")
    return v


# ---------------------------
# backend.hcl meta read
# ---------------------------

def read_backend_meta_test_via_ui(backend_hcl: Path) -> bool | None:
    """
    Reads '# meta.test_via_ui=true/false' from backend.hcl.
    Returns:
      True/False if found, otherwise None.
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
# S3 empty helpers (handles versioning)
# ---------------------------

def s3_bucket_exists(aws_exe: str, env: dict, bucket: str) -> bool:
    try:
        subprocess.check_call(
            [aws_exe, "s3api", "head-bucket", "--bucket", bucket],
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except Exception:
        return False


def s3_empty_bucket(aws_exe: str, env: dict, bucket: str):
    if not bucket:
        return

    bucket = parse_bucket_name(bucket)

    if not s3_bucket_exists(aws_exe, env, bucket):
        warn(f"Bucket not found or not accessible: {bucket} (skipping empty)")
        return

    info(f"Emptying S3 bucket: {bucket}")

    # best-effort non-versioned delete
    try:
        run([aws_exe, "s3", "rm", f"s3://{bucket}", "--recursive"], env=env)
    except SystemExit:
        warn("aws s3 rm failed; continuing with versioned deletion...")

    key_markers = {"KeyMarker": None, "VersionIdMarker": None}

    while True:
        cmd = [aws_exe, "s3api", "list-object-versions", "--bucket", bucket, "--output", "json"]
        if key_markers["KeyMarker"]:
            cmd += ["--key-marker", key_markers["KeyMarker"]]
        if key_markers["VersionIdMarker"]:
            cmd += ["--version-id-marker", key_markers["VersionIdMarker"]]

        data = capture_json(cmd, env=env) or {}

        versions = data.get("Versions", []) or []
        markers = data.get("DeleteMarkers", []) or []

        to_delete = []
        for v in versions:
            k = v.get("Key")
            vid = v.get("VersionId")
            if k and vid:
                to_delete.append({"Key": k, "VersionId": vid})

        for m in markers:
            k = m.get("Key")
            vid = m.get("VersionId")
            if k and vid:
                to_delete.append({"Key": k, "VersionId": vid})

        for i in range(0, len(to_delete), 1000):
            chunk = to_delete[i:i + 1000]
            payload = {"Objects": chunk, "Quiet": True}
            run([aws_exe, "s3api", "delete-objects", "--bucket", bucket, "--delete", json.dumps(payload)], env=env)

        if not bool(data.get("IsTruncated")):
            break

        key_markers["KeyMarker"] = data.get("NextKeyMarker")
        key_markers["VersionIdMarker"] = data.get("NextVersionIdMarker")

        if not key_markers["KeyMarker"] and not key_markers["VersionIdMarker"]:
            warn("Pagination markers missing while IsTruncated=true. Stopping to avoid infinite loop.")
            break

    ok(f"Bucket emptied: {bucket}")


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

    region = questionary.text("AWS region:", default="eu-central-1").ask()
    if not region:
        die("Region required.")
    env["AWS_REGION"] = region
    env["AWS_DEFAULT_REGION"] = region
    env["TF_VAR_region"] = region
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
        warn("If needed, recreate backend.hcl or run provisioning script once to generate it.")

    # Read meta.test_via_ui from backend.hcl
    meta_test_via_ui = read_backend_meta_test_via_ui(backend_hcl)
    if meta_test_via_ui is None:
        warn("meta.test_via_ui not found in backend.hcl -> assuming UI was NOT deployed.")
        meta_test_via_ui = False
    ok(f"meta.test_via_ui={meta_test_via_ui}")

    # Init ROOT for outputs/destroy
    info("Initializing ROOT terraform (best effort)...")
    init_cmd = [terraform_exe, "init"]
    if backend_hcl.exists():
        init_cmd = [terraform_exe, "init", "-reconfigure", f"-backend-config={backend_hcl.name}"]

    try:
        subprocess.check_call(init_cmd, cwd=str(ROOT), env=env)
    except Exception as e:
        warn(f"ROOT terraform init failed (continuing): {e}")

    # Try to get website bucket ONLY if UI was deployed (meta true).
    website_bucket = ""
    if meta_test_via_ui:
        website_bucket = tf_output_soft(terraform_exe, env, str(ROOT), "website_bucket_name") or ""
        if not website_bucket:
            warn("website_bucket_name output not found -> site likely not deployed; skipping s3_website empty.")

    # Step 1: empty website bucket if present
    if website_bucket:
        info("Step 1/4: Empty website bucket (s3_website)")
        s3_empty_bucket(aws_exe, env, website_bucket)
    else:
        info("Step 1/4: No website bucket to empty (skipped)")

    # Step 2: destroy ROOT
    tf_vars = [f"profile={aws_profile}", f"region={region}"]
    info("Step 2/4: Destroy ROOT infrastructure")
    destroy_root_cmd = [terraform_exe, "destroy", "-auto-approve"] + [f"-var={v}" for v in tf_vars]

    run(destroy_root_cmd, cwd=str(ROOT), env=env)
    ok("ROOT infrastructure destroyed")

    # Now init BOOT (only now) to read backend bucket output
    info("Initializing BOOTSTRAP terraform (best effort, for backend bucket output)...")
    boot_init_cmd = [terraform_exe, "init"]
    try:
        subprocess.check_call(boot_init_cmd, cwd=str(BOOT), env=env)
    except Exception as e:
        warn(f"BOOT terraform init failed (continuing): {e}")

    backend_bucket = (
        tf_output_soft(terraform_exe, env, str(BOOT), "backend_s3_bucket_name")
        or tf_output_soft(terraform_exe, env, str(BOOT), "backend_s3_bucket_arn")
        or ""
    )

    # Step 3: empty tf state bucket
    info("Step 3/4: Empty terraform state bucket (s3_tf_state)")
    if backend_bucket:
        s3_empty_bucket(aws_exe, env, backend_bucket)
    else:
        warn("Bootstrap backend bucket output not found (skipping state bucket empty).")

    # Step 4: destroy BOOT
    info("Step 4/4: Destroy BOOTSTRAP infrastructure")
    destroy_boot_cmd = [terraform_exe, "destroy", "-auto-approve"] + [f"-var={v}" for v in tf_vars]

    run(destroy_boot_cmd, cwd=str(BOOT), env=env)
    ok("BOOTSTRAP infrastructure destroyed")

    ok("All done. Infrastructure removed.")


if __name__ == "__main__":
    main()
