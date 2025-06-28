# Bedrock Knowledge Base
resource "aws_bedrock_knowledge_base" "gym_chatbot" {
  name = "${var.environment}-${var.knowledge_base_name}"
  
  knowledge_base_configuration {
    type = "VECTOR"
    vector_knowledge_base_configuration {
      embedding_model_arn = "arn:aws:bedrock:${data.aws_region.current.name}::foundation-model/amazon.titan-embed-text-v1"
    }
  }

  storage_configuration {
    type = "S3"
    s3_configuration {
      bucket_arn = var.s3_bucket_arn
    }
  }

  tags = merge(var.tags, {
    Name = "${var.environment}-${var.knowledge_base_name}"
  })
}

# Data source for current region
data "aws_region" "current" {}

# Output the model ID for reference
locals {
  model_id = var.bedrock_model_id
} 