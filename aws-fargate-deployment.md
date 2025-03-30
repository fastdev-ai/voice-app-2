# AWS Fargate Deployment Guide

This guide provides instructions for deploying the Voice App to AWS Fargate using Python 3.12.

## Prerequisites

- AWS CLI installed and configured
- Docker installed locally
- An AWS ECR repository to store your Docker image
- AWS ECS cluster set up for Fargate

## Step 1: Build and Tag the Docker Image

```bash
# Build the Docker image
docker build -t voice-app .

# Tag the image for your ECR repository
docker tag voice-app:latest <your-aws-account-id>.dkr.ecr.<your-region>.amazonaws.com/voice-app:latest
```

## Step 2: Push to Amazon ECR

```bash
# Login to your ECR repository
aws ecr get-login-password --region <your-region> | docker login --username AWS --password-stdin <your-aws-account-id>.dkr.ecr.<your-region>.amazonaws.com

# Push the image
docker push <your-aws-account-id>.dkr.ecr.<your-region>.amazonaws.com/voice-app:latest
```

## Step 3: Create Task Definition

Create a task definition for Fargate with the following specifications:

1. Use the ECR image URI from Step 2

2. Configure environment variables (this is the standard way to parameterize Fargate containers):
   - `OPENAI_API_KEY`: Your OpenAI API key (use AWS Secrets Manager)
   - `PORT`: 5001 (or your preferred port)
   - `HOST`: 0.0.0.0 (required for container networking)
   - `FLASK_DEBUG`: false
   - `FLASK_ENV`: production
   - `UPLOAD_FOLDER`: /app/recordings
   - `COST_PER_MINUTE`: 0.006
   - `CONFIRM_DELETE`: false
   - `TITLE`: Your preferred app title

3. Configure port mappings:
   - Container port: 5001 (or match your PORT environment variable)
   - Host port: 5001 (or match your PORT environment variable)
   - Protocol: tcp

4. Configure persistent storage:
   - Add an EFS volume mount for /app/recordings if you want to persist recordings
   
5. Configure container health check:
   - Command: CMD-SHELL, curl -f http://localhost:${PORT}/ || exit 1
   - Interval: 30 seconds
   - Timeout: 5 seconds
   - Retries: 3
   - Start period: 10 seconds

## Step 4: Create ECS Service

1. Create a new service in your ECS cluster
2. Select the Fargate launch type
3. Select the task definition created in Step 3
4. Configure networking:
   - VPC: Select your VPC
   - Subnets: Select at least two subnets
   - Security groups: Create or select a security group that allows inbound traffic on port 5001
5. Configure load balancing:
   - Application Load Balancer
   - Target group: Create a new target group
   - Path pattern: /*
   - Health check path: /

## Step 5: Set Up Security

1. Create an IAM role for the task with permissions to:
   - Access ECR
   - Access CloudWatch Logs
   - Access EFS (if using)
   - Access Secrets Manager (for the OpenAI API key)

2. Configure environment variables from AWS Secrets Manager:
   - Use the AWS Secrets Manager to store sensitive information like API keys
   - Configure your task definition to inject these secrets as environment variables
   - Example: Use the `valueFrom` field in the task definition to reference a secret ARN

3. Configure HTTPS:
   - Set up an SSL certificate in AWS Certificate Manager
   - Configure your load balancer to use HTTPS

## Step 6: Monitor Your Application

- Set up CloudWatch alarms for CPU and memory usage
- Configure log groups to collect application logs

## Security Considerations

- Store sensitive information like API keys in AWS Secrets Manager
- Restrict access to your ECS tasks using security groups
- Use IAM roles with least privilege
- Enable AWS CloudTrail for auditing
- Consider implementing AWS WAF for additional security

## Cost Optimization

- Use Fargate Spot instances for non-critical workloads
- Set up auto-scaling based on CPU/memory utilization
- Use AWS Cost Explorer to monitor spending
- Consider using Application Auto Scaling to scale based on custom metrics
- Use AWS Budgets to set cost thresholds and receive alerts

## Environment Variable Management

Environment variables are the standard way to parameterize Fargate containers. Here are some best practices:

1. **AWS Systems Manager Parameter Store**:
   - Store non-sensitive configuration in Parameter Store
   - Reference parameters in your task definition
   - Organize parameters hierarchically (e.g., /voice-app/prod/PORT)

2. **AWS Secrets Manager**:
   - Store sensitive information like API keys
   - Reference secrets in your task definition
   - Rotate secrets regularly

3. **Environment Variable Files**:
   - Create environment variable files for different environments (dev, staging, prod)
   - Use these files with the AWS CLI when creating or updating task definitions

4. **Service Discovery**:
   - Use AWS Cloud Map for service discovery if your application needs to discover other services
   - Configure environment variables for service endpoints
