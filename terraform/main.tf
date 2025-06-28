terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# Data sources
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# S3 Module for document storage
module "s3" {
  source = "./modules/s3"
  
  bucket_name = var.s3_bucket_name
  environment = var.environment
  tags        = var.tags
}

# IAM Module for permissions
module "iam" {
  source = "./modules/iam"
  
  environment = var.environment
  tags        = var.tags
}

# Bedrock Module for AI models and knowledge base
module "bedrock" {
  source = "./modules/bedrock"
  
  environment = var.environment
  knowledge_base_name = var.knowledge_base_name
  bedrock_model_id = var.bedrock_model_id
  s3_bucket_arn = module.s3.bucket_arn
  tags = var.tags
}

# Outputs
output "s3_bucket_name" {
  description = "Name of the S3 bucket for document storage"
  value       = module.s3.bucket_name
}

output "knowledge_base_id" {
  description = "ID of the Bedrock Knowledge Base"
  value       = module.bedrock.knowledge_base_id
}

output "bedrock_model_id" {
  description = "ID of the Bedrock model being used"
  value       = module.bedrock.model_id
}

output "iam_role_arn" {
  description = "ARN of the IAM role for Bedrock access"
  value       = module.iam.bedrock_role_arn
} 