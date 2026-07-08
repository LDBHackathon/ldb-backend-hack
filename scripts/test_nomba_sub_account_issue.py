"""Reproduce and diagnose Nomba sub-account creation failures.

Usage:
  python scripts/test_nomba_sub_account_issue.py
  python scripts/test_nomba_sub_account_issue.py --attempts 3 --name "LDB Debug User"
  python scripts/test_nomba_sub_account_issue.py --env-file .env-hack
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import httpx


def _log(label: str, payload: dict) -> None:
    sys.stdout.write(f"{label} {json.dumps(payload, default=str)}\n")
    sys.stdout.flush()


def _load_env_file(env_file: str) -> None:
    path = Path(env_file)
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def _required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        msg = f"Missing required env var: {name}"
        raise RuntimeError(msg)
    return value


async def _issue_token(
    client: httpx.AsyncClient,
    *,
    base_url: str,
    account_id: str,
    client_id: str,
    client_secret: str,
) -> tuple[str | None, dict]:
    url = f"{base_url}/v1/auth/token/issue"
    headers = {"Content-Type": "application/json", "accountId": account_id}
    payload = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
    }
    response = await client.post(url, headers=headers, json=payload)
    body_text = response.text
    parsed = {}
    try:
        parsed = response.json()
    except Exception:
        parsed = {"raw": body_text}

    token = None
    if isinstance(parsed, dict):
        data = parsed.get("data", {})
        if isinstance(data, dict):
            token = data.get("access_token")

    _log(
        "[TOKEN]",
        {
            "status_code": response.status_code,
            "ok": response.is_success,
            "url": url,
            "response_body": parsed,
        },
    )
    return token, parsed


async def _create_sub_account(
    client: httpx.AsyncClient,
    *,
    base_url: str,
    account_id: str,
    token: str,
    account_name: str,
    account_ref: str,
) -> dict:
    url = f"{base_url}/v1/accounts/sub-account"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "accountId": account_id,
    }
    payload = {"accountName": account_name, "accountRef": account_ref}
    response = await client.post(url, headers=headers, json=payload)
    parsed: dict | str
    try:
        parsed = response.json()
    except Exception:
        parsed = response.text

    result = {
        "status_code": response.status_code,
        "ok": response.is_success,
        "url": url,
        "payload": payload,
        "response_body": parsed,
    }
    _log("[SUB_ACCOUNT_CREATE]", result)
    return result


async def main() -> int:
    parser = argparse.ArgumentParser(description="Diagnose Nomba sub-account create failures.")
    parser.add_argument("--env-file", default=".env", help="Env file path (default: .env)")
    parser.add_argument("--attempts", type=int, default=1, help="Number of create attempts")
    parser.add_argument("--name", default="LDB Debug Account", help="Sub-account name")
    parser.add_argument(
        "--base-url",
        default="",
        help="Override NOMBA_BASE_URL from env",
    )
    args = parser.parse_args()

    _load_env_file(args.env_file)

    base_url = (args.base_url or _required_env("NOMBA_BASE_URL")).rstrip("/")
    account_id = _required_env("NOMBA_ACCOUNT_ID")
    client_id = _required_env("NOMBA_CLIENT_ID")
    client_secret = _required_env("NOMBA_CLIENT_SECRET")

    _log(
        "[CONFIG]",
        {
            "base_url": base_url,
            "account_id": account_id,
            "client_id_prefix": client_id[:8],
            "attempts": args.attempts,
            "timestamp_utc": datetime.now(UTC).isoformat(),
        },
    )

    timeout = httpx.Timeout(30.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        token, _ = await _issue_token(
            client,
            base_url=base_url,
            account_id=account_id,
            client_id=client_id,
            client_secret=client_secret,
        )
        if not token:
            _log("[RESULT]", {"success": False, "reason": "Token request failed"})
            return 1

        failures = 0
        for idx in range(args.attempts):
            account_ref = uuid4().hex
            account_name = f"{args.name[:50]}-{idx + 1}"
            result = await _create_sub_account(
                client,
                base_url=base_url,
                account_id=account_id,
                token=token,
                account_name=account_name,
                account_ref=account_ref,
            )
            if not result["ok"]:
                failures += 1

        _log(
            "[RESULT]",
            {
                "success": failures == 0,
                "attempts": args.attempts,
                "failures": failures,
            },
        )
        return 0 if failures == 0 else 2


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
