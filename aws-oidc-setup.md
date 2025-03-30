# Setting Up GitHub Actions with AWS OIDC Authentication

This guide explains how to set up secure authentication between GitHub Actions and AWS using OpenID Connect (OIDC), which eliminates the need to store long-lived AWS credentials as GitHub secrets.

## Benefits of OIDC Authentication

- **No stored AWS access keys**: Eliminates the security risk of long-lived credentials
- **Automatic credential rotation**: Temporary credentials are generated for each workflow run
- **Fine-grained access control**: Limit permissions based on repository, branch, or environment
- **Improved security posture**: Follows AWS security best practices

## Prerequisites

- AWS account with permissions to create IAM resources
- GitHub repository with GitHub Actions workflows
- AWS CLI installed locally (for setup)

## Setup Instructions

### 1. Create an OIDC Identity Provider in AWS

You can create the OIDC provider using the AWS Management Console or AWS CLI:

```bash
aws iam create-open-id-connect-provider \
  --url https://token.actions.githubusercontent.com \
  --client-id-list sts.amazonaws.com \
  --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1
```

Note: The thumbprint may change over time. Check the [GitHub documentation](https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/configuring-openid-connect-in-amazon-web-services) for the current thumbprint.

### 2. Create an IAM Role for GitHub Actions

Create a new IAM role with the following trust policy (replace placeholders with your values):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::${AWS::AccountId}:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:YOUR_GITHUB_USERNAME/voice-app-2:*"
        }
      }
    }
  ]
}
```

For better security, you can restrict the role to specific branches or environments:

```json
"StringLike": {
  "token.actions.githubusercontent.com:sub": "repo:YOUR_GITHUB_USERNAME/voice-app-2:ref:refs/heads/main"
}
```

### 3. Attach Permissions to the IAM Role

Attach the necessary AWS permissions to the role. For CDK deployment, you'll need permissions for CloudFormation, S3, ECR, and other services used in your stack.

You can start with the `AdministratorAccess` policy for testing, but for production, create a custom policy with only the required permissions.

### 4. Update Your GitHub Actions Workflow

Update your workflow file (`.github/workflows/deploy.yml`) to use OIDC authentication:

```yaml
jobs:
  deploy:
    # ...
    permissions:
      id-token: write  # Required for OIDC
      contents: read   # Required to check out the repository
    
    steps:
      # ...
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          role-to-assume: arn:aws:iam::${{ vars.AWS_ACCOUNT_ID }}:role/GitHubActionsRole
          aws-region: ${{ vars.AWS_REGION }}
      # ...
```

### 5. Set Up GitHub Variables (Not Secrets)

Instead of using secrets for the AWS account ID and region, you can use GitHub repository variables:

1. Go to your repository on GitHub
2. Click on "Settings" → "Secrets and variables" → "Actions"
3. Click on the "Variables" tab
4. Add variables for `AWS_ACCOUNT_ID` and `AWS_REGION`

## Security Considerations

- The AWS account ID is considered sensitive but not secret. Using variables instead of secrets is acceptable.
- Restrict the IAM role to specific GitHub repositories, branches, or environments.
- Apply the principle of least privilege by granting only the permissions needed for your workflow.
- Regularly audit and rotate any remaining long-lived credentials.

## Troubleshooting

If you encounter issues with OIDC authentication:

1. Check the IAM role trust policy for correct GitHub repository name
2. Verify that the workflow has the required permissions (`id-token: write`)
3. Ensure the role has the necessary AWS permissions for your deployment
4. Check CloudTrail logs for authentication failures

## References

- [GitHub Actions: Configuring OpenID Connect in AWS](https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/configuring-openid-connect-in-amazon-web-services)
- [AWS IAM: Creating OpenID Connect (OIDC) identity providers](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_providers_create_oidc.html)
