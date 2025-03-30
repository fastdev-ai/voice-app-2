#!/usr/bin/env python3
import os
from aws_cdk import App, Environment, Aspects
from cdk_nag import AwsSolutionsChecks

from stack import InfrastructureStack

app = App()

# Define the AWS environment (account/region)
env = Environment(
    account=os.environ.get("CDK_DEFAULT_ACCOUNT", ""),
    region=os.environ.get("CDK_DEFAULT_REGION", "us-east-2")
)

# Instantiate the main infrastructure stack
InfrastructureStack(app, "GeneratedInfrastructure",
    description="Infrastructure generated by AI-DevOps",
    env=env
)

# Add the following line after each stack is defined to apply CDK-NAG checks
# cdk_nag = AwsSolutionsChecks(verbose=True)
# cdk_nag.visit(stack)

app.synth()
