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
    table_name = os.environ.get("DDB_TABLE")
    if not table_name:
        raise RuntimeError("Missing env var DDB_TABLE")
    return dynamodb.Table(table_name)

def lambda_handler(event, context):
    """
    POST /messages
    Expects JSON body like:
      {
        "text": "hello",
        "author": "piero"   (optional)
      }
    Creates:
      message_id (uuid)
      created_at (ISO8601)
    """
    try:
        table = _table()

        raw_body = event.get("body")
        if raw_body is None:
            return _response(400, {"error": "MissingBody"})

        # HTTP API may send isBase64Encoded; handle both
        if event.get("isBase64Encoded"):
            import base64
            raw_body = base64.b64decode(raw_body).decode("utf-8")

        try:
            payload = json.loads(raw_body)
        except json.JSONDecodeError:
            return _response(400, {"error": "InvalidJSON"})

        text = payload.get("text")
        if not isinstance(text, str) or not text.strip():
            return _response(400, {"error": "ValidationError", "field": "text"})

        author = payload.get("author")
        if author is not None and not isinstance(author, str):
            return _response(400, {"error": "ValidationError", "field": "author"})

        item = {
            "message_id": str(uuid.uuid4()),
            "text": text.strip(),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        if author:
            item["author"] = author.strip()

        # ConditionExpression ensures we don't overwrite an existing id (very unlikely with uuid)
        try:
            table.put_item(
                Item=item,
                ConditionExpression="attribute_not_exists(message_id)"
            )
        except ClientError as e:
            code = e.response.get("Error", {}).get("Code", "")
            if code == "ConditionalCheckFailedException":
                return _response(409, {"error": "Conflict", "message": "ID already exists"})
            return _response(500, {"error": "DDBPutItemFailed", "detail": str(e)})

        return _response(201, item)

    except Exception as e:
        return _response(500, {"error": "Unhandled", "detail": str(e)})