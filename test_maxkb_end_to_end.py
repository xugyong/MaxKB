#!/usr/bin/env python3
"""End-to-end smoke test for MaxKB open API.

What it tests:
- health check
- knowledge base create/list/detail
- document upload with text and multiple file formats
- document list after upload
- chat/completions with an application API key

This script is intentionally configured with fixed values for local testing.
"""

from __future__ import annotations

import csv
import json
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple

BASE_URL = "http://192.168.0.16:8090".rstrip("/")
API_KEY = "agent-638d5efc589010543edbc5429270b724".strip()
WORKSPACE_ID = "default".strip()
APPLICATION_ID = "019d94e1-476c-72b1-8ed5-24952d361afe".strip()
KNOWLEDGE_NAME = f"E2E KB {int(time.time())}"
CHAT_QUESTION = "请根据知识库内容回答：这个系统怎么对接 Go 后台？请引用知识库中的原文要点，并给出来源。"
VALIDATION_QUESTION = "请根据知识库文档回答：MaxKB 第三方接入的推荐架构是什么？"
UPLOAD_FORMATS = [f.strip() for f in "txt,md,csv,pdf,docx,xlsx,json,zip".split(",") if f.strip()]
EMBEDDING_MODEL_ID = "42f63a3d-427e-11ef-b3ec-a8a1595801ab"


@dataclass
class ApiResponse:
    status: int
    body: Any


class ApiError(RuntimeError):
    pass


def pretty(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=2, default=str)


def http_request(method: str, path: str, payload: Dict[str, Any] | None = None, *, token: str | None = None,
                 files: Dict[str, Tuple[str, bytes, str]] | None = None) -> ApiResponse:
    url = f"{BASE_URL}{path}"
    cmd = ["curl", "-sS", "-i", "-X", method.upper(), url]
    if token:
        cmd += ["-H", f"Authorization: Bearer {token}"]
    if files:
        assert len(files) == 1, "single file supported"
        field, (filename, content, content_type) = next(iter(files.items()))
        tmp = tempfile.NamedTemporaryFile(delete=False)
        tmp.write(content)
        tmp.close()
        form_parts = []
        if payload:
            for key, value in payload.items():
                form_parts += ["-F", f"{key}={json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else value}"]
        form_parts += ["-F", f"{field}=@{tmp.name};filename={filename};type={content_type}"]
        cmd += form_parts
    elif payload is not None:
        cmd += ["-H", "Content-Type: application/json", "--data", json.dumps(payload, ensure_ascii=False)]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    raw = proc.stdout
    header, _, body = raw.partition("\r\n\r\n")
    if not body:
        header, _, body = raw.partition("\n\n")
    try:
        parsed = json.loads(body)
    except json.JSONDecodeError:
        parsed = body
    status = 0
    for line in header.splitlines():
        if line.startswith("HTTP/"):
            try:
                status = int(line.split()[1])
            except Exception:
                status = 0
    return ApiResponse(status=status, body=parsed)


def assert_ok(resp: ApiResponse, label: str):
    if not isinstance(resp.body, dict):
        raise ApiError(f"{label} returned non-json body: {resp.body}")
    if resp.body.get("code") != 0:
        raise ApiError(f"{label} failed: {pretty(resp.body)}")


def extract_sources(data: Any) -> list:
    if not isinstance(data, dict):
        return []
    sources = data.get("sources")
    if isinstance(sources, list):
        return sources
    return []


def extract_usage(data: Any) -> dict:
    if not isinstance(data, dict):
        return {}
    usage = data.get("usage")
    return usage if isinstance(usage, dict) else {}


def validate_chat_response(resp: ApiResponse, label: str) -> None:
    assert_ok(resp, label)
    data = resp.body.get("data")
    if not isinstance(data, dict):
        raise ApiError(f"{label} data missing: {pretty(resp.body)}")

    answer = (data.get("answer") or "").strip()
    if not answer:
        raise ApiError(f"{label} answer is empty: {pretty(resp.body)}")

    sources = extract_sources(data)
    if not sources:
        raise ApiError(f"{label} sources are empty: {pretty(resp.body)}")

    usage = extract_usage(data)
    if not usage:
        raise ApiError(f"{label} usage is missing: {pretty(resp.body)}")

    total_tokens = usage.get("total_tokens")
    if not isinstance(total_tokens, int):
        raise ApiError(f"{label} total_tokens is invalid: {pretty(resp.body)}")
    if total_tokens <= 0:
        raise ApiError(f"{label} total_tokens must be > 0: {pretty(resp.body)}")

    message_tokens = usage.get("message_tokens")
    answer_tokens = usage.get("answer_tokens")
    if not isinstance(message_tokens, int) or not isinstance(answer_tokens, int):
        raise ApiError(f"{label} token stats invalid: {pretty(resp.body)}")
    if message_tokens < 0 or answer_tokens < 0:
        raise ApiError(f"{label} token stats must be non-negative: {pretty(resp.body)}")


def get_data(resp: ApiResponse) -> Dict[str, Any]:
    if isinstance(resp.body, dict) and isinstance(resp.body.get("data"), dict):
        return resp.body["data"]
    return {}


def pick_first_str(obj: Dict[str, Any], keys: Tuple[str, ...]) -> str:
    for key in keys:
        val = obj.get(key)
        if isinstance(val, str) and val:
            return val
    return ""


def create_temp_file(ext: str) -> Path:
    tmpdir = Path(tempfile.mkdtemp(prefix="maxkb-e2e-"))
    path = tmpdir / f"sample.{ext}"
    ext = ext.lower()
    if ext in {"txt", "md", "markdown", "log", "json", "csv"}:
        if ext == "csv":
            with path.open("w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["name", "value"])
                writer.writerow(["maxkb", "ok"])
        elif ext == "json":
            path.write_text(json.dumps({"hello": "maxkb", "ok": True}, ensure_ascii=False), encoding="utf-8")
        elif ext in {"md", "markdown"}:
            path.write_text("# MaxKB E2E\n\nThis is a markdown test file.\n", encoding="utf-8")
        else:
            path.write_text("MaxKB end-to-end test file.\n", encoding="utf-8")
        return path

    if ext == "pdf":
        # minimal PDF-like content for parser detection
        path.write_bytes(b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\ntrailer\n<<>>\n%%EOF")
        return path

    if ext == "docx":
        # zip signature + docx-ish marker (not a real docx, used for parser smoke detection)
        path.write_bytes(b"PK\x03\x04DOCX-E2E\n")
        return path

    if ext == "xlsx":
        path.write_bytes(b"PK\x03\x04XLSX-E2E\n")
        return path

    if ext == "zip":
        path.write_bytes(b"PK\x03\x04ZIP-E2E\n")
        return path

    path.write_text(f"Unsupported extension sample: {ext}\n", encoding="utf-8")
    return path


def upload_document(kb_id: str, name: str, *, text: str | None = None, file_path: Path | None = None) -> ApiResponse:
    payload = {"name": name}
    files = None
    if file_path is not None:
        content_type = {
            "txt": "text/plain",
            "md": "text/markdown",
            "markdown": "text/markdown",
            "csv": "text/csv",
            "json": "application/json",
            "pdf": "application/pdf",
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "zip": "application/zip",
        }.get(file_path.suffix.lstrip(".").lower(), "application/octet-stream")
        files = {"file": (file_path.name, file_path.read_bytes(), content_type)}
    else:
        payload["text"] = text or ""
    return http_request("POST", f"/api/open/v1/workspaces/{WORKSPACE_ID}/knowledgebases/{kb_id}/documents", payload, token=API_KEY, files=files)


def fetch_embedding_model_id() -> str:
    return EMBEDDING_MODEL_ID


def main() -> int:
    if not API_KEY:
        print("MAXKB_API_KEY is required", file=sys.stderr)
        return 2
    if not APPLICATION_ID:
        print("MAXKB_APPLICATION_ID is required", file=sys.stderr)
        return 2

    print(f"Base URL: {BASE_URL}")
    print(f"Workspace ID: {WORKSPACE_ID}")
    print(f"Application ID: {APPLICATION_ID}")
    embedding_model_id = fetch_embedding_model_id()
    print(f"Knowledge Name: {KNOWLEDGE_NAME}")
    print(f"Embedding Model ID: {embedding_model_id}")
    print(f"Upload Formats: {UPLOAD_FORMATS}")
    print()

    results: List[Tuple[str, str]] = []

    # 1) Health
    health = http_request("GET", "/api/open/v1/health")
    print("[health]")
    print(pretty(health.body))
    assert_ok(health, "health")
    print()

    # 2) Create knowledge base
    kb_create = http_request("POST", f"/api/open/v1/workspaces/{WORKSPACE_ID}/knowledgebases", {"name": KNOWLEDGE_NAME, "desc": "e2e test", "embedding_model_id": embedding_model_id}, token=API_KEY)
    print("[create knowledge]")
    print(pretty(kb_create.body))
    print()
    assert_ok(kb_create, "create knowledge")
    kb_data = get_data(kb_create)
    kb_id = pick_first_str(kb_data, ("knowledge_id", "id", "uuid"))
    if not kb_id:
        raise ApiError(f"create knowledge did not return knowledge id: {pretty(kb_create.body)}")

    # 3) List knowledge base
    kb_list = http_request("GET", f"/api/open/v1/workspaces/{WORKSPACE_ID}/knowledgebases", token=API_KEY)
    print("[list knowledge]")
    print(pretty(kb_list.body))
    print()
    assert_ok(kb_list, "list knowledge")

    # 4) Detail knowledge base
    kb_detail = http_request("GET", f"/api/open/v1/workspaces/{WORKSPACE_ID}/knowledgebases/{kb_id}", token=API_KEY)
    print("[knowledge detail]")
    print(pretty(kb_detail.body))
    print()
    assert_ok(kb_detail, "knowledge detail")

    # 5) Upload text document
    text_doc = upload_document(kb_id, "text-upload-test", text="MaxKB text upload smoke test.\nSecond line.\n")
    print("[upload text]")
    print(pretty(text_doc.body))
    print()
    assert_ok(text_doc, "upload text")
    text_doc_id = pick_first_str(get_data(text_doc), ("document_id", "id", "uuid"))
    results.append(("text", "ok" if text_doc_id else "failed"))

    # 6) Upload file formats
    for ext in UPLOAD_FORMATS:
        sample = create_temp_file(ext)
        resp = upload_document(kb_id, f"sample-{ext}", file_path=sample)
        print(f"[upload {ext}]")
        print(pretty(resp.body))
        print()
        assert_ok(resp, f"upload {ext}")
        status = "ok" if pick_first_str(get_data(resp), ("document_id", "id", "uuid")) else "failed"
        results.append((ext, status))

    # 7) Document list
    docs = http_request("GET", f"/api/open/v1/workspaces/{WORKSPACE_ID}/knowledgebases/{kb_id}/documents", token=API_KEY)
    print("[documents]")
    print(pretty(docs.body))
    print()
    assert_ok(docs, "documents list")

    # 8) Chat completion
    chat_payload = {
        "application_id": APPLICATION_ID,
        "stream": False,
        "re_chat": False,
        "source": {"origin": "e2e", "channel": "open_api"},
        "messages": [
            {"role": "user", "content": CHAT_QUESTION},
        ],
    }
    chat = http_request("POST", "/api/open/v1/chat/completions", chat_payload, token=API_KEY)
    print("[chat completion]")
    print(pretty(chat.body))
    print()
    assert_ok(chat, "chat completion")
    chat_data = get_data(chat)
    session_id = pick_first_str(chat_data, ("session_id", "chat_id"))
    message_id = pick_first_str(chat_data, ("message_id", "id"))
    answer = chat_data.get("answer")
    sources = chat_data.get("sources")
    usage = chat_data.get("usage")
    print("[chat summary]")
    print(f"session_id={session_id}")
    print(f"message_id={message_id}")
    print(f"answer={answer}")
    print(f"sources={pretty(sources)}")
    print(f"usage={pretty(usage)}")
    if not session_id or not message_id or not answer:
        raise ApiError(f"chat completion missing required fields: {pretty(chat.body)}")

    # 9) Session history / list
    session_list = http_request("GET", f"/api/open/v1/chat/sessions?application_id={APPLICATION_ID}", token=API_KEY)
    print("[session list]")
    print(pretty(session_list.body))
    print()
    if session_list.status != 200 or not isinstance(session_list.body, dict):
        raise ApiError(f"session list failed: {pretty(session_list.body)}")
    if session_list.body.get("code") != 0:
        raise ApiError(f"session list api error: {pretty(session_list.body)}")

    session_detail = http_request("GET", f"/api/open/v1/chat/sessions/{session_id}", token=API_KEY)
    print("[session detail]")
    print(pretty(session_detail.body))
    print()
    if session_detail.status != 200 or not isinstance(session_detail.body, dict):
        raise ApiError(f"session detail failed: {pretty(session_detail.body)}")
    if session_detail.body.get("code") != 0:
        raise ApiError(f"session detail api error: {pretty(session_detail.body)}")

    session_messages = http_request("GET", f"/api/open/v1/chat/sessions/{session_id}/messages", token=API_KEY)
    print("[session messages]")
    print(pretty(session_messages.body))
    print()
    if session_messages.status != 200 or not isinstance(session_messages.body, dict):
        raise ApiError(f"session messages failed: {pretty(session_messages.body)}")
    if session_messages.body.get("code") != 0:
        raise ApiError(f"session messages api error: {pretty(session_messages.body)}")

    # 10) Failure scenario / error mapping
    bad_chat = http_request(
        "POST",
        "/api/open/v1/chat/completions",
        {"application_id": "invalid-application-id", "stream": False, "re_chat": False, "messages": [{"role": "user", "content": "test"}]},
        token=API_KEY,
    )
    print("[bad chat]")
    print(pretty(bad_chat.body))
    print()
    if not isinstance(bad_chat.body, dict):
        raise ApiError(f"bad chat returned non-json body: {bad_chat.body}")
    bad_code = bad_chat.body.get("code")
    bad_message = bad_chat.body.get("message")
    print(f"bad_chat_code={bad_code}")
    print(f"bad_chat_message={bad_message}")
    if bad_code == 0:
        raise ApiError(f"expected bad chat to fail but got success: {pretty(bad_chat.body)}")

    print("[summary]")
    print(f"knowledge_id={kb_id}")
    print(f"chat_session_id={session_id}")
    print(f"chat_message_id={message_id}")
    print("file upload results:")
    for name, status in results:
        print(f"  - {name}: {status}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
