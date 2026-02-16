import json
import os
import boto3
from botocore.exceptions import ClientError

dynamodb = boto3.resource("dynamodb")


def _response(status_code: int, body: dict | list | str):
    if not isinstance(body, (dict, list)):
        body = {"text": str(body)}
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
    Supports:
      - GET /messages            -> returns a page of items (SCAN, limited)
      - GET /messages/{id}       -> returns a single item by message_id
    HTTP API v2 event format.
    """
    print("=== READER start ===")
    print("[ctx] function:", getattr(context, "function_name", None))
    print("[ctx] request_id:", getattr(context, "aws_request_id", None))

    try:
        # Basic event shape
        print("[event] top-level keys:", list(event.keys()) if isinstance(event, dict) else type(event))
        print("[event] version:", event.get("version"))
        print("[event] routeKey:", event.get("routeKey"))
        print("[event] rawPath:", event.get("rawPath"))
        print("[event] rawQueryString:", event.get("rawQueryString"))

        rc = event.get("requestContext") or {}
        http = (rc.get("http") or {})
        print("[event] http.method:", http.get("method"))
        print("[event] http.path:", http.get("path"))
        print("[event] stage:", rc.get("stage"))

        # Headers (just show a few)
        headers = event.get("headers") or {}
        print("[event] headers keys:", list(headers.keys())[:20])

        table = _table()

        # HTTP API v2 route parameters
        path_params = event.get("pathParameters") or {}
        msg_id = path_params.get("id")
        print("[route] pathParameters:", _safe_json(path_params))
        print("[route] msg_id:", msg_id)

        if msg_id:
            print("[ddb] get_item Key:", {"message_id": msg_id})
            try:
                resp = table.get_item(Key={"message_id": msg_id})
                print("[ddb] get_item response keys:", list(resp.keys()))
            except ClientError as e:
                print("[error] DDB get_item ClientError:", repr(e))
                return _response(500, {"error": "DDBGetItemFailed", "detail": str(e)})

            item = resp.get("Item")
            print("[ddb] item found:", bool(item))
            if not item:
                return _response(404, {"error": "NotFound", "message_id": msg_id})

            return _response(200, item)

        # Get all (simple scan with limit)
        limit = 50
        qs = event.get("queryStringParameters") or {}
        print("[route] queryStringParameters:", _safe_json(qs))

        if qs.get("limit"):
            try:
                limit = max(1, min(200, int(qs["limit"])))
            except ValueError:
                print("[warn] invalid limit:", qs.get("limit"))
                return _response(400, {"error": "InvalidLimit"})

        scan_kwargs = {"Limit": limit}
        print("[ddb] scan_kwargs initial:", _safe_json(scan_kwargs))

        # Pagination token (string you return to the client)
        next_token = qs.get("next_token")
        if next_token:
            print("[ddb] next_token received (len):", len(next_token))
            try:
                scan_kwargs["ExclusiveStartKey"] = json.loads(next_token)
                print("[ddb] ExclusiveStartKey:", _safe_json(scan_kwargs["ExclusiveStartKey"]))
            except json.JSONDecodeError:
                print("[warn] InvalidNextToken JSONDecodeError")
                return _response(400, {"error": "InvalidNextToken"})

        try:
            resp = table.scan(**scan_kwargs)
            print("[ddb] scan response keys:", list(resp.keys()))
        except ClientError as e:
            print("[error] DDB scan ClientError:", repr(e))
            return _response(500, {"error": "DDBScanFailed", "detail": str(e)})

        items = resp.get("Items", [])
        lek = resp.get("LastEvaluatedKey")
        print("[ddb] items count:", len(items))
        print("[ddb] LastEvaluatedKey present:", bool(lek))

        return _response(200, {
            "items": items,
            "next_token": json.dumps(lek) if lek else None
        })

    except Exception as e:
        print("[fatal] Unhandled exception:", repr(e))
        return _response(500, {"error": "Unhandled", "detail": str(e)})
    finally:
        print("=== READER end ===")