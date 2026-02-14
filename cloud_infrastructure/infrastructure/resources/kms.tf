data "aws_iam_policy_document" "kms_key_policy" {
  statement {

    effect = "Allow"

    actions = [
      "kms:Encrypt",
      "kms:Decrypt",
      "kms:GenerateDataKey",
      "kms:DescribeKey"
    ]

    resources = [
      "*"
    ]

    principals {
      type        = "AWS"
      identifiers = [module.lambda_reader_iam.role_arn, module.lambda_writer_iam.role_arn]
    }
  }
}

resource "aws_kms_key" "key" {
  description = "KMS key for encrypting messages"
  policy      = data.aws_iam_policy_document.kms_key_policy.json

  enable_key_rotation = true
}