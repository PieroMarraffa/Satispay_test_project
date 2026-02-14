import json
import os
import uuid
from datetime import datetime, timezone

import boto3
from botocore.exceptions import ClientError

dynamodb = boto3.resource("dynamodb")


def _response(status_code: int, body: dict | list | str):
    if not isinstance(body, (dict, list)):
        body = {"message": str(body)}
    return {
        "statusCode": status_code,
        "headers": {
            "content-type": "application/json"
        },
        "body": json.dumps(body),
    }


def _table():
    table_name = os.environ.get("DDB_TABLE") or os.environ.get("DDB_TABLE_NAME")
    print("[table] env DDB_TABLE:", os.environ.get("DDB_TABLE"))
    print("[table] env DDB_TABLE_NAME:", os.environ.get("DDB_TABLE_NAME"))
    if not table_name:
        raise RuntimeError("Missing env var DDB_TABLE (or DDB_TABLE_NAME)")
    print("[table] using table:", table_name)
    return dynamodb.Table(table_name)


def _safe_json(obj, max_len=2000):
    try:
        s = json.dumps(obj, default=str)
        return s if len(s) <= max_len else s[:max_len] + "...(truncated)"
    except Exception:
        return "<unserializable>"


def lambda_handler(event, context):
    """
    POST /messages
    Expects JSON body like:
      { "text": "hello", "author": "piero" (optional) }
    """
    print("=== WRITER start ===")
    print("[ctx] function:", getattr(context, "function_name", None))
    print("[ctx] request_id:", getattr(context, "aws_request_id", None))

    try:
        print("[event] top-level keys:", list(event.keys()) if isinstance(event, dict) else type(event))
        print("[event] version:", event.get("version"))
        print("[event] routeKey:", event.get("routeKey"))
        print("[event] rawPath:", event.get("rawPath"))

        rc = event.get("requestContext") or {}
        http = (rc.get("http") or {})
        print("[event] http.method:", http.get("method"))
        print("[event] http.path:", http.get("path"))
        print("[event] stage:", rc.get("stage"))

        headers = event.get("headers") or {}
        print("[event] headers keys:", list(headers.keys())[:20])

        table = _table()

        raw_body = event.get("body")
        print("[body] present:", raw_body is not None)
        if raw_body is None:
            return _response(400, {"error": "MissingBody"})

        is_b64 = bool(event.get("isBase64Encoded"))
        print("[body] isBase64Encoded:", is_b64)
        print("[body] raw length:", len(raw_body) if isinstance(raw_body, str) else type(raw_body))

        if is_b64:
            import base64
            raw_body = base64.b64decode(raw_body).decode("utf-8")
            print("[body] decoded length:", len(raw_body))

        # Don't print whole body; just a small snippet
        if isinstance(raw_body, str):
            print("[body] snippet:", raw_body[:200])

        try:
            payload = json.loads(raw_body)
            print("[body] payload keys:", list(payload.keys()) if isinstance(payload, dict) else type(payload))
        except json.JSONDecodeError as e:
            print("[warn] InvalidJSON:", repr(e))
            return _response(400, {"error": "InvalidJSON"})

        text = payload.get("text")
        print("[validate] text type:", type(text).__name__)
        if not isinstance(text, str) or not text.strip():
            return _response(400, {"error": "ValidationError", "field": "text"})

        author = payload.get("author")
        print("[validate] author type:", type(author).__name__ if author is not None else None)
        if author is not None and not isinstance(author, str):
            return _response(400, {"error": "ValidationError", "field": "author"})

        item = {
            "message_id": str(uuid.uuid4()),
            "text": text.strip(),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        if author and isinstance(author, str) and author.strip():
            item["author"] = author.strip()

        print("[ddb] put_item item:", _safe_json(item))

        try:
            resp = table.put_item(
                Item=item,
                ConditionExpression="attribute_not_exists(message_id)"
            )
            print("[ddb] put_item response keys:", list(resp.keys()))
        except ClientError as e:
            print("[error] DDB put_item ClientError:", repr(e))
            code = e.response.get("Error", {}).get("Code", "")
            print("[error] DDB error code:", code)
            if code == "ConditionalCheckFailedException":
                return _response(409, {"error": "Conflict", "message": "ID already exists"})
            return _response(500, {"error": "DDBPutItemFailed", "detail": str(e)})

        return _response(201, item)

    except Exception as e:
        print("[fatal] Unhandled exception:", repr(e))
        return _response(500, {"error": "Unhandled", "detail": str(e)})
    finally:
        print("=== WRITER end ===")