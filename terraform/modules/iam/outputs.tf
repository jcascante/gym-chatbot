output "bedrock_role_arn" {
  description = "ARN of the IAM role for Bedrock access"
  value       = aws_iam_role.bedrock_role.arn
}

output "bedrock_role_name" {
  description = "Name of the IAM role for Bedrock access"
  value       = aws_iam_role.bedrock_role.name
}

output "app_user_name" {
  description = "Name of the IAM user for application access"
  value       = aws_iam_user.app_user.name
}

output "app_user_access_key_id" {
  description = "Access key ID for the application user"
  value       = aws_iam_access_key.app_user_key.id
  sensitive   = true
}

output "app_user_secret_access_key" {
  description = "Secret access key for the application user"
  value       = aws_iam_access_key.app_user_key.secret
  sensitive   = true
} 