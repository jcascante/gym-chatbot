# IAM Role for Bedrock access
resource "aws_iam_role" "bedrock_role" {
  name = "${var.environment}-gym-chatbot-bedrock-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "bedrock.amazonaws.com"
        }
      }
    ]
  })

  tags = merge(var.tags, {
    Name = "${var.environment}-gym-chatbot-bedrock-role"
  })
}

# IAM Policy for Bedrock permissions
resource "aws_iam_policy" "bedrock_policy" {
  name        = "${var.environment}-gym-chatbot-bedrock-policy"
  description = "Policy for Bedrock model invocation and knowledge base access"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream"
        ]
        Resource = [
          "arn:aws:bedrock:${data.aws_region.current.name}::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0",
          "arn:aws:bedrock:${data.aws_region.current.name}::foundation-model/anthropic.claude-3-haiku-20240307-v1:0",
          "arn:aws:bedrock:${data.aws_region.current.name}::foundation-model/anthropic.claude-3-opus-20240229-v1:0"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "bedrock:Retrieve",
          "bedrock:RetrieveAndGenerate"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          "arn:aws:s3:::gym-chatbot-documents",
          "arn:aws:s3:::gym-chatbot-documents/*"
        ]
      }
    ]
  })
}

# Attach policy to role
resource "aws_iam_role_policy_attachment" "bedrock_policy_attachment" {
  role       = aws_iam_role.bedrock_role.name
  policy_arn = aws_iam_policy.bedrock_policy.arn
}

# IAM User for application access (if needed)
resource "aws_iam_user" "app_user" {
  name = "${var.environment}-gym-chatbot-app-user"

  tags = merge(var.tags, {
    Name = "${var.environment}-gym-chatbot-app-user"
  })
}

# Access key for the application user
resource "aws_iam_access_key" "app_user_key" {
  user = aws_iam_user.app_user.name
}

# Policy for application user
resource "aws_iam_user_policy" "app_user_policy" {
  name = "${var.environment}-gym-chatbot-app-policy"
  user = aws_iam_user.app_user.name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream"
        ]
        Resource = [
          "arn:aws:bedrock:${data.aws_region.current.name}::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0",
          "arn:aws:bedrock:${data.aws_region.current.name}::foundation-model/anthropic.claude-3-haiku-20240307-v1:0",
          "arn:aws:bedrock:${data.aws_region.current.name}::foundation-model/anthropic.claude-3-opus-20240229-v1:0"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "bedrock:Retrieve",
          "bedrock:RetrieveAndGenerate"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:ListBucket"
        ]
        Resource = [
          "arn:aws:s3:::gym-chatbot-documents",
          "arn:aws:s3:::gym-chatbot-documents/*"
        ]
      }
    ]
  })
}

# Data sources
data "aws_region" "current" {} 