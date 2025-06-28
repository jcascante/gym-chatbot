#!/bin/bash

# Gym Chatbot - Terraform Deployment Script
# This script automates the deployment of AWS infrastructure

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check if AWS CLI is installed
    if ! command -v aws &> /dev/null; then
        print_error "AWS CLI is not installed. Please install it first."
        exit 1
    fi
    
    # Check if Terraform is installed
    if ! command -v terraform &> /dev/null; then
        print_error "Terraform is not installed. Please install it first."
        exit 1
    fi
    
    # Check if AWS credentials are configured
    if ! aws sts get-caller-identity &> /dev/null; then
        print_error "AWS credentials are not configured. Please run 'aws configure' first."
        exit 1
    fi
    
    print_success "All prerequisites are met!"
}

# Initialize Terraform
init_terraform() {
    print_status "Initializing Terraform..."
    terraform init
    print_success "Terraform initialized successfully!"
}

# Plan Terraform deployment
plan_terraform() {
    print_status "Planning Terraform deployment..."
    terraform plan
    print_success "Terraform plan completed!"
}

# Apply Terraform deployment
apply_terraform() {
    print_status "Applying Terraform deployment..."
    terraform apply -auto-approve
    print_success "Terraform deployment completed!"
}

# Get outputs and save to file
save_outputs() {
    print_status "Saving Terraform outputs..."
    
    # Create outputs directory if it doesn't exist
    mkdir -p outputs
    
    # Save outputs to JSON file
    terraform output -json > outputs/terraform_outputs.json
    
    # Extract key values for environment variables
    cat > outputs/environment_vars.env << EOF
# AWS Configuration
AWS_REGION=$(terraform output -raw aws_region 2>/dev/null || echo "us-east-1")
AWS_ACCESS_KEY_ID=$(terraform output -raw app_user_access_key_id 2>/dev/null || echo "")
AWS_SECRET_ACCESS_KEY=$(terraform output -raw app_user_secret_access_key 2>/dev/null || echo "")

# Bedrock Configuration
KNOWLEDGE_BASE_ID=$(terraform output -raw knowledge_base_id 2>/dev/null || echo "")
BEDROCK_MODEL_ID=$(terraform output -raw bedrock_model_id 2>/dev/null || echo "")

# S3 Configuration
S3_BUCKET_NAME=$(terraform output -raw s3_bucket_name 2>/dev/null || echo "")
EOF

    print_success "Outputs saved to outputs/ directory!"
}

# Main deployment function
deploy() {
    print_status "Starting deployment of Gym Chatbot infrastructure..."
    
    check_prerequisites
    init_terraform
    plan_terraform
    
    echo
    read -p "Do you want to proceed with the deployment? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        apply_terraform
        save_outputs
        
        echo
        print_success "Deployment completed successfully!"
        echo
        print_status "Next steps:"
        echo "1. Copy the environment variables from outputs/environment_vars.env to your .env file"
        echo "2. Run the document ingestion script: python scripts/ingest_documents.py"
        echo "3. Start your application with the new environment variables"
        echo
        print_status "You can find all outputs in the outputs/ directory"
    else
        print_warning "Deployment cancelled by user"
        exit 0
    fi
}

# Destroy function
destroy() {
    print_warning "This will destroy all AWS resources created by Terraform!"
    read -p "Are you sure you want to proceed? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Destroying infrastructure..."
        terraform destroy -auto-approve
        print_success "Infrastructure destroyed successfully!"
    else
        print_warning "Destruction cancelled by user"
    fi
}

# Show help
show_help() {
    echo "Gym Chatbot - Terraform Deployment Script"
    echo
    echo "Usage: $0 [COMMAND]"
    echo
    echo "Commands:"
    echo "  deploy   - Deploy the infrastructure (default)"
    echo "  destroy  - Destroy the infrastructure"
    echo "  plan     - Show the deployment plan"
    echo "  init     - Initialize Terraform"
    echo "  help     - Show this help message"
    echo
}

# Main script logic
case "${1:-deploy}" in
    "deploy")
        deploy
        ;;
    "destroy")
        destroy
        ;;
    "plan")
        check_prerequisites
        init_terraform
        plan_terraform
        ;;
    "init")
        check_prerequisites
        init_terraform
        ;;
    "help"|"-h"|"--help")
        show_help
        ;;
    *)
        print_error "Unknown command: $1"
        show_help
        exit 1
        ;;
esac 