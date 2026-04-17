#!/usr/bin/env python3
"""Local smoke test for MaxKB.

This script is intended for local development verification against either:
- the Docker compose stack (default: http://127.0.0.1:8090)
- the Django dev server (set BASE_URL=http://127.0.0.1:8080 and BASE_PREFIX=/admin)

What it checks:
- health endpoint
- frontend static availability
- captcha endpoint
- login endpoint
- authenticated profile/session endpoints
- representative authenticated APIs that are safe for local verification

It prints a compact summary and exits non-zero if any critical step fails.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from typing import Any, Dict, Tuple
from urllib.parse import urljoin


@dataclass
class Response:
    status: int
    body: Any
    headers: Dict[str, str]


class SmokeTestError(RuntimeError):
    pass


DEFAULT_BASE_URL = "http://127.0.0.1:8090"
DEFAULT_PREFIX = "/admin"
DEFAULT_USERNAME = "admin"
DEFAULT_PASSWORD = "admin"
DEFAULT_WORKSPACE_ID = "default"
DEFAULT_APPLICATION_ID = ""
DEFAULT_API_KEY = ""


def run_curl(method: str, url: str, *, token: str | None = None, json_body: Any | None = None) -> Response:
    cmd = ["curl", "-sS", "-i", "-X", method.upper(), url]
    if token:
        cmd += ["-H", f"Authorization: Bearer {token}"]
    if json_body is not None:
        cmd += ["-H", "Content-Type: application/json", "--data", json.dumps(json_body, ensure_ascii=False)]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    raw = proc.stdout
    header_text, _, body = raw.partition("\r\n\r\n")
    if not body:
        header_text, _, body = raw.partition("\n\n")

    status = 0
    headers: Dict[str, str] = {}
    for line in header_text.splitlines():
        if line.startswith("HTTP/"):
            try:
                status = int(line.split()[1])
            except Exception:
                status = 0
        elif ":" in line:
            key, value = line.split(":", 1)
            headers[key.strip().lower()] = value.strip()

    try:
        parsed_body = json.loads(body)
    except Exception:
        parsed_body = body

    return Response(status=status, body=parsed_body, headers=headers)


def expect_json(resp: Response, label: str) -> Dict[str, Any]:
    if not isinstance(resp.body, dict):
        raise SmokeTestError(f"{label} did not return JSON: {resp.body}")
    return resp.body


def expect_ok(resp: Response, label: str) -> Dict[str, Any]:
    body = expect_json(resp, label)
    if body.get("code") != 0:
        raise SmokeTestError(f"{label} failed: {json.dumps(body, ensure_ascii=False, indent=2)}")
    return body


def build_url(base: str, path: str) -> str:
    if path.startswith("http://") or path.startswith("https://"):
        return path
    return urljoin(base + "/", path.lstrip("/"))


def print_step(title: str, resp: Response) -> None:
    print(f"[{title}] status={resp.status}")
    if isinstance(resp.body, (dict, list)):
        print(json.dumps(resp.body, ensure_ascii=False, indent=2))
    else:
        print(resp.body)
    print()


def login(base_url: str, prefix: str, username: str, password: str) -> Tuple[str, Response, Response]:
    captcha_resp = run_curl("GET", build_url(base_url, f"{prefix}/api/user/captcha?username={username}"))
    print_step("captcha", captcha_resp)
    captcha_body = expect_json(captcha_resp, "captcha")
    captcha = ""
    if isinstance(captcha_body.get("data"), dict):
        captcha = captcha_body["data"].get("captcha", "") or ""
    elif isinstance(captcha_body.get("data"), str):
        captcha = captcha_body["data"]

    payload = {
        "username": username,
        "password": password,
        "captcha": captcha,
    }
    login_resp = run_curl("POST", build_url(base_url, f"{prefix}/api/user/login"), json_body=payload)
    print_step("login", login_resp)
    login_body = expect_ok(login_resp, "login")
    data = login_body.get("data") or {}
    token = ""
    if isinstance(data, dict):
        token = data.get("token") or data.get("access_token") or data.get("auth_token") or ""
    if not token and isinstance(login_body.get("token"), str):
        token = login_body["token"]
    if not token:
        raise SmokeTestError(f"login succeeded but no token found: {json.dumps(login_body, ensure_ascii=False, indent=2)}")
    return token, captcha_resp, login_resp


def main() -> int:
    parser = argparse.ArgumentParser(description="Run local MaxKB smoke tests")
    args = parser.parse_args([])

    base_url = DEFAULT_BASE_URL.rstrip("/")
    prefix = DEFAULT_PREFIX if DEFAULT_PREFIX.startswith("/") else f"/{DEFAULT_PREFIX}"

    print(f"Base URL: {base_url}")
    print(f"Prefix: {prefix}")
    print(f"Username: {DEFAULT_USERNAME}")
    print()

    steps = []

    health = run_curl("GET", build_url(base_url, f"{prefix}/api/open/v1/health"))
    print_step("health", health)
    expect_ok(health, "health")
    steps.append("health")

    # Static frontend / route checks
    admin_page = run_curl("GET", build_url(base_url, f"{prefix}/"))
    print_step("admin-ui", admin_page)
    if admin_page.status != 200:
        raise SmokeTestError(f"admin ui failed with HTTP {admin_page.status}")
    steps.append("admin-ui")

    token, _, _ = login(base_url, prefix, DEFAULT_USERNAME, DEFAULT_PASSWORD)
    steps.append("login")

    profile = run_curl("GET", build_url(base_url, f"{prefix}/api/user/profile"), token=token)
    print_step("profile", profile)
    expect_ok(profile, "profile")
    steps.append("profile")

    language = run_curl("GET", build_url(base_url, f"{prefix}/api/user/language"), token=token)
    print_step("language", language)
    if language.status not in (200, 404):
        raise SmokeTestError(f"language endpoint unexpected HTTP {language.status}")
    steps.append("language")

    auth_setting = run_curl("GET", build_url(base_url, f"{prefix}/api/system-settings/auth-setting/login-auth-setting"), token=token)
    print_step("login-auth-setting", auth_setting)
    if auth_setting.status not in (200, 404):
        raise SmokeTestError(f"auth setting endpoint unexpected HTTP {auth_setting.status}")
    steps.append("login-auth-setting")

    print("[skip] Open API checks are disabled in this local-only script\n")

    print("[summary]")
    print("Passed steps:")
    for step in steps:
        print(f"  - {step}")
    print("Local system is ready.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SmokeTestError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
