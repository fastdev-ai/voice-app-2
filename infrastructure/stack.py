from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_ecs_patterns as ecs_patterns,
    aws_iam as iam,
    aws_dynamodb as dynamodb,
    aws_s3 as s3,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    aws_secretsmanager as secretsmanager,
    RemovalPolicy,
    CfnOutput,
    Duration
)
from constructs import Construct

class InfrastructureStack(Stack):

    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Create a VPC with public and private subnets
        vpc = ec2.Vpc(self, "MyVpc",
                      max_azs=2,
                      nat_gateways=1,
                      subnet_configuration=[
                          ec2.SubnetConfiguration(
                              name="PublicSubnet",
                              subnet_type=ec2.SubnetType.PUBLIC,
                              cidr_mask=24
                          ),
                          ec2.SubnetConfiguration(
                              name="PrivateSubnet",
                              subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                              cidr_mask=24
                          )
                      ])

        # Create an S3 bucket for storage
        bucket = s3.Bucket(self, "MyBucket",
                           versioned=True,
                           removal_policy=RemovalPolicy.DESTROY,
                           auto_delete_objects=True)

        # Create a DynamoDB table
        table = dynamodb.Table(self, "MyTable",
                               partition_key=dynamodb.Attribute(
                                   name="id",
                                   type=dynamodb.AttributeType.STRING),
                               billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST)

        # Create an ECS cluster
        cluster = ecs.Cluster(self, "MyCluster", vpc=vpc)

        # Define IAM role for ECS task execution
        task_execution_role = iam.Role(self, "TaskExecutionRole",
                                       assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
                                       managed_policies=[
                                           iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AmazonECSTaskExecutionRolePolicy")
                                       ])

        # Define IAM role for ECS task
        task_role = iam.Role(self, "TaskRole",
                             assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
                             managed_policies=[
                                 iam.ManagedPolicy.from_aws_managed_policy_name("AmazonDynamoDBFullAccess"),
                                 iam.ManagedPolicy.from_aws_managed_policy_name("AmazonS3FullAccess")
                             ])

        # Reference the existing OpenAI API key secret
        openai_api_key_secret = secretsmanager.Secret.from_secret_name_v2(
            self, "OpenAIAPIKeySecret", "OPENAI_API_KEY"
        )

        # Create an Application Load Balanced Fargate Service
        fargate_service = ecs_patterns.ApplicationLoadBalancedFargateService(self, "MyFargateService",
                                                                             cluster=cluster,
                                                                             cpu=256,
                                                                             memory_limit_mib=512,
                                                                             desired_count=2,
                                                                             task_image_options={
                                                                                 "image": ecs.ContainerImage.from_asset(
                                                                                     "../",
                                                                                     exclude=[
                                                                                         "cdk.out",          # CDK output directory
                                                                                         ".git",             # Git repository data
                                                                                         ".github",          # GitHub Actions workflows
                                                                                         ".idea",            # IDE configuration
                                                                                         "infrastructure",   # CDK infrastructure code
                                                                                         "README.md",        # Documentation
                                                                                         "aws-fargate-deployment.md", # Documentation
                                                                                         "aws-oidc-setup.md",  # Documentation
                                                                                         "docker-compose.yml", # Local development config
                                                                                         ".dockerignore",    # Docker build instructions (not needed in final image)
                                                                                         ".gitignore",       # Git ignore rules
                                                                                         ".env.example",     # Example environment file
                                                                                         ".env.template",    # Template environment file
                                                                                         "voice-recorder.service", # Systemd service file
                                                                                         "~"                 # Stray directory?
                                                                                     ]
                                                                                 ),
                                                                                 "execution_role": task_execution_role,
                                                                                 "task_role": task_role,
                                                                                 "container_port": 5001,  # Match the port in your Dockerfile
                                                                                 "secrets": {
                                                                                     "OPENAI_API_KEY": ecs.Secret.from_secrets_manager(openai_api_key_secret)
                                                                                 },
                                                                                 "environment": {
                                                                                     "PORT": "5001",
                                                                                     "HOST": "0.0.0.0",
                                                                                     "FLASK_ENV": "production"
                                                                                 }
                                                                             },
                                                                             public_load_balancer=True)

        # Allow the Fargate service to access the DynamoDB table
        table.grant_read_write_data(fargate_service.task_definition.task_role)

        # Create a CloudFront distribution pointing to the ALB
        distribution = cloudfront.Distribution(self, "MyDistribution",
                                               default_behavior={
                                                   "origin": origins.LoadBalancerV2Origin(
                                                       fargate_service.load_balancer,
                                                       protocol_policy=cloudfront.OriginProtocolPolicy.HTTP_ONLY,
                                                       http_port=80,
                                                       connection_attempts=3,
                                                       connection_timeout=Duration.seconds(10)
                                                   ),
                                                   "viewer_protocol_policy": cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                                                   "allowed_methods": cloudfront.AllowedMethods.ALLOW_ALL, # Allow POST, DELETE etc.
                                                   "cache_policy": cloudfront.CachePolicy.CACHING_DISABLED, # Disable caching for dynamic app
                                                   "origin_request_policy": cloudfront.OriginRequestPolicy.ALL_VIEWER
                                               })

        # Allow traffic from anywhere to the ALB (CloudFront needs this)
        fargate_service.service.connections.security_groups[0].add_ingress_rule(
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port.tcp(80),
            description="Allow HTTP traffic from anywhere (including CloudFront)"
        )

        # Output the CloudFront distribution domain name
        CfnOutput(self, "DistributionDomainName",
                  value=distribution.distribution_domain_name,
                  description="The domain name of the CloudFront distribution")