variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "s3_bucket_name" {
  description = "Name for the S3 bucket (must be globally unique)"
  type        = string
  default     = "gym-chatbot-documents"
}

variable "bedrock_model_id" {
  description = "Bedrock model ID to use for inference"
  type        = string
  default     = "anthropic.claude-3-sonnet-20240229-v1:0"
}

variable "knowledge_base_name" {
  description = "Name for the Bedrock Knowledge Base"
  type        = string
  default     = "gym-chatbot-knowledge-base"
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default = {
    Project     = "gym-chatbot"
    Environment = "dev"
    ManagedBy   = "terraform"
  }
} 