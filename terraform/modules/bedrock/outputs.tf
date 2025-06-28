output "knowledge_base_id" {
  description = "ID of the Bedrock Knowledge Base"
  value       = aws_bedrock_knowledge_base.gym_chatbot.knowledge_base_id
}

output "knowledge_base_arn" {
  description = "ARN of the Bedrock Knowledge Base"
  value       = aws_bedrock_knowledge_base.gym_chatbot.arn
}

output "knowledge_base_name" {
  description = "Name of the Bedrock Knowledge Base"
  value       = aws_bedrock_knowledge_base.gym_chatbot.name
}

output "model_id" {
  description = "Bedrock model ID being used"
  value       = local.model_id
} 