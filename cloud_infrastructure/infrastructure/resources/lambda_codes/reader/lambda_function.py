import json
import os
import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key

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
    Supports:
      - GET /messages            -> returns a page of items (SCAN, limited)
      - GET /messages/{id}       -> returns a single item by message_id
    HTTP API v2 event format.
    """
    try:
        table = _table()

        # HTTP API v2 route parameters
        path_params = event.get("pathParameters") or {}
        msg_id = path_params.get("id")

        if msg_id:
            # Get single item
            try:
                resp = table.get_item(Key={"message_id": msg_id})
            except ClientError as e:
                return _response(500, {"error": "DDBGetItemFailed", "detail": str(e)})

            item = resp.get("Item")
            if not item:
                return _response(404, {"error": "NotFound", "message_id": msg_id})

            return _response(200, item)

        # Get all (simple scan with limit)
        # NOTE: SCAN is not ideal for big tables; consider adding a partition design/GSI later.
        limit = 50
        qs = event.get("queryStringParameters") or {}
        if qs.get("limit"):
            try:
                limit = max(1, min(200, int(qs["limit"])))
            except ValueError:
                return _response(400, {"error": "InvalidLimit"})

        scan_kwargs = {"Limit": limit}

        # Pagination token (base64-ish string you return to the client)
        next_token = qs.get("next_token")
        if next_token:
            try:
                scan_kwargs["ExclusiveStartKey"] = json.loads(next_token)
            except json.JSONDecodeError:
                return _response(400, {"error": "InvalidNextToken"})

        try:
            resp = table.scan(**scan_kwargs)
        except ClientError as e:
            return _response(500, {"error": "DDBScanFailed", "detail": str(e)})

        items = resp.get("Items", [])
        last_evaluated_key = resp.get("LastEvaluatedKey")

        return _response(200, {
            "items": items,
            "next_token": json.dumps(last_evaluated_key) if last_evaluated_key else None
        })

    except Exception as e:
        return _response(500, {"error": "Unhandled", "detail": str(e)})