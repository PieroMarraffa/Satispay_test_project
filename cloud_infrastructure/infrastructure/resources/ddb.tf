resource "aws_dynamodb_table" "messages_table" {
    name         = "messages_table"
    billing_mode = "PAY_PER_REQUEST"
    tags        = var.tags

    hash_key = "message_id"

    attribute {
        name = "message_id"
        type = "S"
    }

    server_side_encryption {
        enabled     = true
        kms_key_arn = aws_kms_key.key.arn
    }
}