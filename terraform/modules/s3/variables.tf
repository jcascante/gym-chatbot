variable "bucket_name" {
  description = "Name of the S3 bucket for document storage"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
} 