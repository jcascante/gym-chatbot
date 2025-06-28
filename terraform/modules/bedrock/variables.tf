variable "environment" {
  description = "Environment name"
  type        = string
}

variable "knowledge_base_name" {
  description = "Name for the Bedrock Knowledge Base"
  type        = string
  default     = "gym-chatbot-knowledge-base"
}

variable "bedrock_model_id" {
  description = "Bedrock model ID to use for inference"
  type        = string
  default     = "anthropic.claude-3-sonnet-20240229-v1:0"
}

variable "s3_bucket_arn" {
  description = "ARN of the S3 bucket for knowledge base storage"
  type        = string
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
} 