"""Alibaba Cloud DashScope file upload utility.

Uploads a local file to DashScope's temporary OSS storage and returns an oss:// URL.
URL is valid for 48 hours and can be used with DashScope model APIs.

Steps:
  1. GET /api/v1/uploads?action=getPolicy&model=<model_name>  → OSS policy
  2. POST <policy.upload_host> multipart/form-data with file  → OSS URL

Reference: https://help.aliyun.com/zh/model-studio/get-temporary-file-url
"""
from __future__ import annotations

import os
import time
from pathlib import Path

import requests

_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
_POLICY_URL = "https://dashscope.aliyuncs.com/api/v1/uploads"


def get_upload_policy(api_key: str, model_name: str) -> dict:
    """Step 1: Get OSS upload policy for the given model."""
    resp = requests.get(
        _POLICY_URL,
        headers={"Authorization": f"Bearer {api_key}"},
        params={"action": "getPolicy", "model": model_name},
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    if "data" not in data:
        raise RuntimeError(f"Upload policy error: {data}")
    return data["data"]


def upload_to_oss(policy: dict, file_path: Path) -> str:
    """Step 2: Upload file to OSS using policy credentials. Returns oss:// URL."""
    file_name = file_path.name
    key = f"{policy['upload_dir']}/{file_name}"

    with open(file_path, "rb") as f:
        files = {
            "key": (None, key),
            "OSSAccessKeyId": (None, policy["oss_access_key_id"]),
            "Signature": (None, policy["signature"]),
            "policy": (None, policy["policy"]),
            "x-oss-object-acl": (None, policy.get("x_oss_object_acl", "default")),
            "x-oss-forbid-overwrite": (None, policy.get("x_oss_forbid_overwrite", "false")),
            "success_action_status": (None, "200"),
            "Content-Disposition": (None, "attachment"),
            "file": (file_name, f, "application/octet-stream"),
        }
        resp = requests.post(policy["upload_host"], files=files, timeout=60)

    if resp.status_code not in (200, 204):
        raise RuntimeError(f"OSS upload failed ({resp.status_code}): {resp.text[:300]}")

    bucket = policy["upload_host"].split("//")[1].split(".")[0]
    return f"oss://{bucket}/{key}"


def upload_file(file_path: str | Path, model_name: str, api_key: str = "") -> str:
    """Upload a local file and return its oss:// URL (valid 48h)."""
    key = api_key or _API_KEY
    if not key:
        raise ValueError("DASHSCOPE_API_KEY not set")
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    ts = time.strftime("%H:%M:%S")
    print(f"  [Upload {ts}] {path.name} → model={model_name}")
    policy = get_upload_policy(key, model_name)
    oss_url = upload_to_oss(policy, path)
    print(f"  [Upload] → {oss_url}")
    return oss_url
