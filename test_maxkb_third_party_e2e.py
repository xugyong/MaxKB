#!/usr/bin/env python3
"""Third-party integration end-to-end smoke test for MaxKB.

This script is intentionally close in style to `test_maxkb_end_to_end.py`:
- fixed local values
- simple HTTP calls through curl
- explicit step-by-step assertions
- intended to verify the third-party integration contract

It focuses on the flows described in the integration docs:
- health
- create/list/detail knowledge base
- text upload + representative file upload
- document list
- chat/completions
- session list/detail/messages
- optional failure mapping for invalid application_id
"""

from __future__ import annotations

import csv
import json
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple

BASE_URL = "http://127.0.0.1:8080".rstrip("/")
API_KEY = "agent-ffddad5b6a737d7b7e3064874717b02f".strip()
WORKSPACE_ID = "default".strip()
APPLICATION_ID = "019d95c2-7d9a-7183-b237-9ba530a33ebd".strip()
KNOWLEDGE_NAME = f"Third Party E2E KB {int(time.time())}"
CHAT_QUESTION = "请根据知识库内容回答：第三方 Go 后台如何调用 MaxKB？请返回来源和关键步骤。"
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


def http_request(
    method: str,
    path: str,
    payload: Dict[str, Any] | None = None,
    *,
    token: str | None = None,
    files: Dict[str, Tuple[str, bytes, str]] | None = None,
) -> ApiResponse:
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
    tmpdir = Path(tempfile.mkdtemp(prefix="maxkb-third-party-e2e-"))
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
            path.write_text("# MaxKB Third Party E2E\n\nThis is a markdown test file.\n", encoding="utf-8")
        else:
            path.write_text("MaxKB third-party end-to-end test file.\n", encoding="utf-8")
        return path

    if ext == "pdf":
        path.write_bytes(b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\ntrailer\n<<>>\n%%EOF")
        return path

    if ext == "docx":
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


def main() -> int:
    print(f"Base URL: {BASE_URL}")
    print(f"Workspace ID: {WORKSPACE_ID}")
    print(f"Application ID: {APPLICATION_ID}")
    print(f"Knowledge Name: {KNOWLEDGE_NAME}")
    print(f"Embedding Model ID: {EMBEDDING_MODEL_ID}")
    print(f"Upload Formats: {UPLOAD_FORMATS}")
    print()

    results: List[Tuple[str, str]] = []

    health = http_request("GET", "/api/open/v1/health")
    print("[health]")
    print(pretty(health.body))
    assert_ok(health, "health")
    print()

    kb_create = http_request(
        "POST",
        f"/api/open/v1/workspaces/{WORKSPACE_ID}/knowledgebases",
        {"name": KNOWLEDGE_NAME, "desc": "third-party e2e test", "embedding_model_id": EMBEDDING_MODEL_ID},
        token=API_KEY,
    )
    print("[create knowledge]")
    print(pretty(kb_create.body))
    print()
    assert_ok(kb_create, "create knowledge")
    kb_data = get_data(kb_create)
    kb_id = pick_first_str(kb_data, ("knowledge_id", "id", "uuid"))
    if not kb_id:
        raise ApiError(f"create knowledge did not return knowledge id: {pretty(kb_create.body)}")

    kb_list = http_request("GET", f"/api/open/v1/workspaces/{WORKSPACE_ID}/knowledgebases", token=API_KEY)
    print("[list knowledge]")
    print(pretty(kb_list.body))
    print()
    assert_ok(kb_list, "list knowledge")

    kb_detail = http_request("GET", f"/api/open/v1/workspaces/{WORKSPACE_ID}/knowledgebases/{kb_id}", token=API_KEY)
    print("[knowledge detail]")
    print(pretty(kb_detail.body))
    print()
    assert_ok(kb_detail, "knowledge detail")

    text_doc = upload_document(kb_id, "text-upload-test", text="MaxKB text upload smoke test.\nSecond line.\n")
    print("[upload text]")
    print(pretty(text_doc.body))
    print()
    assert_ok(text_doc, "upload text")
    text_doc_id = pick_first_str(get_data(text_doc), ("document_id", "id", "uuid"))
    results.append(("text", "ok" if text_doc_id else "failed"))

    for ext in UPLOAD_FORMATS:
        sample = create_temp_file(ext)
        resp = upload_document(kb_id, f"sample-{ext}", file_path=sample)
        print(f"[upload {ext}]")
        print(pretty(resp.body))
        print()
        assert_ok(resp, f"upload {ext}")
        status = "ok" if pick_first_str(get_data(resp), ("document_id", "id", "uuid")) else "failed"
        results.append((ext, status))

    docs = http_request("GET", f"/api/open/v1/workspaces/{WORKSPACE_ID}/knowledgebases/{kb_id}/documents", token=API_KEY)
    print("[documents]")
    print(pretty(docs.body))
    print()
    assert_ok(docs, "documents list")

    chat_payload = {
        "application_id": APPLICATION_ID,
        "stream": False,
        "re_chat": False,
        "source": {"origin": "third-party-e2e", "channel": "open_api"},
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
    if not sources:
        raise ApiError(f"chat completion missing sources: {pretty(chat.body)}")

    session_list = http_request("GET", f"/api/open/v1/chat/sessions?application_id={APPLICATION_ID}", token=API_KEY)
    print("[session list]")
    print(pretty(session_list.body))
    print()
    if session_list.status != 200 or not isinstance(session_list.body, dict):
        raise ApiError(f"session list failed: {pretty(session_list.body)}")
    if session_list.body.get("code") != 0:
        raise ApiError(f"session list api error: {pretty(session_list.body)}")
    session_list_data = get_data(session_list)
    session_items = session_list_data.get("items") if isinstance(session_list_data, dict) else []
    if not isinstance(session_items, list):
        raise ApiError(f"session list items invalid: {pretty(session_list.body)}")
    if len(session_items) == 0:
        print(f"[warn] session list empty, fallback to detail lookup for {session_id}")
    else:
        if not any(isinstance(item, dict) and str(item.get("id")) == str(session_id) for item in session_items):
            print(f"[warn] session list does not contain created session {session_id}, fallback to detail lookup")

    session_detail = http_request("GET", f"/api/open/v1/chat/sessions/{session_id}", token=API_KEY)
    print("[session detail]")
    print(pretty(session_detail.body))
    print()
    if session_detail.status != 200 or not isinstance(session_detail.body, dict):
        raise ApiError(f"session detail failed: {pretty(session_detail.body)}")
    if session_detail.body.get("code") != 0:
        raise ApiError(f"session detail api error: {pretty(session_detail.body)}")
    session_detail_data = get_data(session_detail)
    if str(session_detail_data.get("session_id")) != str(session_id):
        raise ApiError(f"session detail id mismatch: expected {session_id}, got {pretty(session_detail_data)}")
    if str(session_detail_data.get("application_id")) != str(APPLICATION_ID):
        raise ApiError(f"session detail application mismatch: expected {APPLICATION_ID}, got {pretty(session_detail_data)}")

    session_messages = http_request("GET", f"/api/open/v1/chat/sessions/{session_id}/messages", token=API_KEY)
    print("[session messages]")
    print(pretty(session_messages.body))
    print()
    if session_messages.status != 200 or not isinstance(session_messages.body, dict):
        raise ApiError(f"session messages failed: {pretty(session_messages.body)}")
    if session_messages.body.get("code") != 0:
        raise ApiError(f"session messages api error: {pretty(session_messages.body)}")
    session_messages_data = get_data(session_messages)
    message_items = session_messages_data.get("items") if isinstance(session_messages_data, dict) else []
    if not isinstance(message_items, list) or len(message_items) == 0:
        raise ApiError(f"session messages are empty: {pretty(session_messages.body)}")
    if not any(isinstance(item, dict) and (item.get("answer_text") or item.get("problem_text")) for item in message_items):
        raise ApiError(f"session messages missing content: {pretty(session_messages.body)}")

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

    chat_session_detail = http_request("GET", f"/api/open/v1/chat/sessions/{session_id}", token=API_KEY)
    print("[post-bad session recheck]")
    print(pretty(chat_session_detail.body))
    print()
    assert_ok(chat_session_detail, "post-bad session recheck")

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
