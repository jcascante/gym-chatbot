# Gym Chatbot - AWS Infrastructure as Code

This directory contains Terraform modules to deploy all AWS resources needed for the gym chatbot application.

## Architecture Overview

The infrastructure includes:

- **S3 Bucket**: For storing documents that will be ingested into the knowledge base
- **Bedrock Knowledge Base**: For RAG (Retrieval Augmented Generation) functionality
- **IAM Roles and Policies**: For secure access to AWS services
- **Bedrock Models**: For AI inference (Claude 3 models)

## Prerequisites

1. **AWS CLI** installed and configured
2. **Terraform** >= 1.0 installed
3. **AWS Account** with appropriate permissions
4. **Bedrock Access**: Ensure your AWS account has access to Bedrock models

## Quick Start

1. **Clone and navigate to the terraform directory**:
   ```bash
   cd terraform
   ```

2. **Copy the example variables file**:
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   ```

3. **Edit terraform.tfvars** with your specific values:
   ```hcl
   aws_region = "us-east-1"
   environment = "dev"
   s3_bucket_name = "your-unique-gym-chatbot-documents-bucket"
   ```

4. **Initialize Terraform**:
   ```bash
   terraform init
   ```

5. **Plan the deployment**:
   ```bash
   terraform plan
   ```

6. **Apply the infrastructure**:
   ```bash
   terraform apply
   ```

## Configuration

### Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `aws_region` | AWS region for all resources | `us-east-1` | No |
| `environment` | Environment name (dev, staging, prod) | `dev` | No |
| `s3_bucket_name` | S3 bucket name (must be globally unique) | `gym-chatbot-documents` | No |
| `bedrock_model_id` | Bedrock model ID for inference | `anthropic.claude-3-sonnet-20240229-v1:0` | No |
| `knowledge_base_name` | Name for the Bedrock Knowledge Base | `gym-chatbot-knowledge-base` | No |

### Environment Variables

After deployment, you'll need to set these environment variables in your application:

```bash
AWS_REGION=<aws_region>
AWS_ACCESS_KEY_ID=<access_key_id>
AWS_SECRET_ACCESS_KEY=<secret_access_key>
KNOWLEDGE_BASE_ID=<knowledge_base_id>
BEDROCK_MODEL_ID=<model_id>
```

## Modules

### S3 Module (`./modules/s3`)

Creates an S3 bucket for document storage with:
- Versioning enabled
- Server-side encryption
- Public access blocked
- Bucket policy for Bedrock access

### IAM Module (`./modules/iam`)

Creates IAM resources:
- Role for Bedrock service access
- User for application access
- Policies with minimal required permissions

### Bedrock Module (`./modules/bedrock`)

Creates Bedrock resources:
- Knowledge Base with vector search
- Configuration for document ingestion

## Security Features

- **Encryption**: All data is encrypted at rest and in transit
- **Least Privilege**: IAM policies grant only necessary permissions
- **Public Access Blocked**: S3 bucket is private by default
- **Resource Tagging**: All resources are tagged for cost tracking

## Cost Optimization

- **S3 Lifecycle**: Consider adding lifecycle policies for cost optimization
- **Bedrock Model Selection**: Choose appropriate models based on your needs
- **Resource Cleanup**: Use `terraform destroy` when not needed

## Troubleshooting

### Common Issues

1. **S3 Bucket Name Already Exists**
   - Change the `s3_bucket_name` variable to a unique name

2. **Bedrock Access Denied**
   - Ensure your AWS account has Bedrock access enabled
   - Request access to specific models if needed

3. **IAM Permissions**
   - Ensure your AWS user/role has permissions to create IAM resources

### Useful Commands

```bash
# View current state
terraform show

# List resources
terraform state list

# Refresh state
terraform refresh

# Destroy infrastructure
terraform destroy
```

## Post-Deployment Steps

1. **Upload Documents**: Upload your gym-related documents to the S3 bucket
2. **Ingest into Knowledge Base**: Use the Bedrock console or API to ingest documents
3. **Update Application**: Update your application's environment variables
4. **Test**: Verify the chatbot can access the knowledge base

## Cleanup

To remove all resources:

```bash
terraform destroy
```

**Warning**: This will permanently delete all resources and data.

## Support

For issues with the infrastructure:
1. Check the Terraform documentation
2. Review AWS service quotas and limits
3. Verify your AWS account permissions 