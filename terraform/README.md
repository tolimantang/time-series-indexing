# AstroFinancial Terraform Infrastructure

This directory contains Terraform configurations for deploying the AstroFinancial application infrastructure on AWS using EKS (Elastic Kubernetes Service).

## Architecture Overview

The infrastructure includes:

- **VPC**: Custom VPC with public, private, and database subnets across 2 AZs
- **EKS Cluster**: Managed Kubernetes cluster with worker nodes
- **RDS PostgreSQL**: Encrypted database with automated backups
- **EFS**: Elastic File System for ChromaDB persistence
- **S3**: Bucket for data backups and storage
- **ECR**: Container registries for API and indexer images
- **KMS**: Encryption keys for all services
- **Security Groups**: Network access controls
- **IAM Roles**: Service accounts and permissions

## Prerequisites

1. **AWS CLI configured** with appropriate credentials
2. **Terraform >= 1.0** installed
3. **kubectl** installed for cluster management
4. **Appropriate AWS permissions** for creating EKS, RDS, VPC, etc.

## Quick Start

1. **Clone and navigate to terraform directory**:
   ```bash
   cd terraform
   ```

2. **Copy and customize variables**:
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   # Edit terraform.tfvars with your values
   ```

3. **Initialize Terraform**:
   ```bash
   terraform init
   ```

4. **Plan the deployment**:
   ```bash
   terraform plan
   ```

5. **Apply the infrastructure**:
   ```bash
   terraform apply
   ```

6. **Configure kubectl**:
   ```bash
   aws eks update-kubeconfig --region us-west-2 --name astro-financial-production-cluster
   ```

## Configuration

### Required Variables

Copy `terraform.tfvars.example` to `terraform.tfvars` and set:

- `aws_region`: AWS region for deployment
- `environment`: Environment name (production, staging, dev)
- `project_name`: Project name for resource naming
- `ssl_certificate_arn`: ACM certificate ARN for HTTPS

### Optional Customizations

- `cluster_version`: Kubernetes version
- `node_instance_types`: EC2 instance types for worker nodes
- `database_instance_class`: RDS instance size
- `vpc_cidr`: VPC network range
- `allowed_cidr_blocks`: IP ranges allowed to access cluster

## Security Features

- **Encryption at rest** for RDS, EFS, S3, and ECR
- **KMS key rotation** enabled
- **Private subnets** for worker nodes and database
- **Security groups** with least privilege access
- **IAM roles** with minimal required permissions
- **VPC endpoints** for cost optimization

## Post-Deployment Steps

1. **Update kubeconfig**:
   ```bash
   terraform output kubectl_config
   # Run the command from the output
   ```

2. **Verify cluster access**:
   ```bash
   kubectl get nodes
   ```

3. **Deploy application**:
   ```bash
   kubectl apply -f ../deploy/k8s/
   ```

4. **Get database credentials**:
   ```bash
   aws secretsmanager get-secret-value --secret-id astro-financial-production-cluster-db-credentials --region us-west-2
   ```

## Resource Scaling

### Node Group Scaling
Modify these variables in `terraform.tfvars`:
```hcl
node_desired_capacity = 3
node_max_capacity = 15
node_min_capacity = 2
```

### Database Scaling
```hcl
database_instance_class = "db.r5.large"
database_max_allocated_storage = 2000
```

## Monitoring and Logging

- **EKS Control Plane Logs**: Enabled for all log types
- **RDS Enhanced Monitoring**: 60-second intervals
- **Performance Insights**: Enabled for RDS
- **VPC Flow Logs**: Available for network monitoring

## Cost Optimization

- **Spot instances** available for non-production environments
- **EFS Intelligent Tiering** for storage cost reduction
- **S3 Lifecycle policies** for long-term data archival
- **VPC endpoints** to reduce NAT Gateway costs

## Backup and Recovery

- **RDS Automated Backups**: 7-day retention (configurable)
- **EFS Point-in-time Recovery**: Available
- **S3 Versioning**: Enabled with lifecycle management
- **Infrastructure as Code**: Complete state in Terraform

## Troubleshooting

### Common Issues

1. **Insufficient Permissions**:
   ```bash
   # Check AWS credentials
   aws sts get-caller-identity
   ```

2. **Cluster Access Issues**:
   ```bash
   # Update kubeconfig
   aws eks update-kubeconfig --region us-west-2 --name <cluster-name>
   ```

3. **Node Group Issues**:
   ```bash
   # Check node group status
   aws eks describe-nodegroup --cluster-name <cluster-name> --nodegroup-name <nodegroup-name>
   ```

### Terraform State Management

For production environments, configure remote state storage:

```hcl
terraform {
  backend "s3" {
    bucket = "your-terraform-state-bucket"
    key    = "eks-cluster/terraform.tfstate"
    region = "us-west-2"
    encrypt = true
  }
}
```

## Cleanup

To destroy the infrastructure:

```bash
# Ensure no critical data will be lost
terraform plan -destroy

# Destroy infrastructure
terraform destroy
```

**Warning**: This will permanently delete all resources including databases and storage. Ensure you have backups if needed.

## Support

For infrastructure issues:
1. Check Terraform logs
2. Review AWS CloudTrail for API errors
3. Verify IAM permissions
4. Check resource limits and quotas

## Security Best Practices

- Enable MFA for AWS accounts
- Use least privilege IAM policies
- Regularly rotate access keys
- Monitor AWS CloudTrail logs
- Keep Terraform and providers updated
- Use encrypted communication channels