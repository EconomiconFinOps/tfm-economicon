variable "project" {
  type    = string
  default = "economicon"
  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{2,14}$", var.project))
    error_message = "Use 3-15 lowercase letters, numbers or hyphens."
  }
}
variable "environment" {
  type    = string
  default = "reference"
  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{1,9}$", var.environment))
    error_message = "Use 2-10 lowercase letters, numbers or hyphens."
  }
}
variable "region" {
  type    = string
  default = "eu-west-1"
}
variable "availability_zones" {
  description = "Three different AZs in region; illustrative names, no availability assumed."
  type        = list(string)
  default     = ["eu-west-1a", "eu-west-1b", "eu-west-1c"]
  validation {
    condition     = length(var.availability_zones) == 3 && length(toset(var.availability_zones)) == 3
    error_message = "Supply three distinct AZs for the MQ cluster."
  }
  validation {
    condition     = alltrue([for az in var.availability_zones : startswith(az, var.region)])
    error_message = "All AZs must belong to region."
  }
}
variable "vpc_cidr" {
  type    = string
  default = "10.60.0.0/16"
  validation {
    condition     = can(cidrsubnet(var.vpc_cidr, 8, 22)) && endswith(var.vpc_cidr, "/16")
    error_message = "Supply an IPv4 /16 VPC CIDR."
  }
}
variable "single_nat_gateway" {
  description = "False: one NAT per AZ. True reduces cost but creates cross-AZ dependency."
  type        = bool
  default     = false
}
variable "route53_zone_id" {
  description = "Existing PUBLIC Route 53 hosted zone containing both domain names."
  type        = string
}
variable "frontend_domain" {
  description = "Example app.example.com. The template creates DNS/certificates only if applied."
  type        = string
}
variable "origin_domain" {
  description = "Example origin.example.com; TLS name for the internal ALB. Must differ from frontend_domain."
  type        = string
  validation {
    condition     = var.origin_domain != var.frontend_domain
    error_message = "Use distinct frontend and origin DNS names."
  }
}
variable "postgres_version" {
  description = "Explicit RDS PostgreSQL version; verify regional support and pgvector before a hypothetical use."
  type        = string
}
variable "postgres_parameter_family" {
  description = "Matching parameter group family, e.g. postgres16."
  type        = string
  validation {
    condition     = var.postgres_parameter_family == "postgres${split(".", var.postgres_version)[0]}"
    error_message = "Parameter group family must match the PostgreSQL major version."
  }
}
variable "db_instance_class" {
  type    = string
  default = "db.t4g.medium"
}
variable "rabbitmq_version" {
  description = "Explicit Amazon MQ RabbitMQ engine version. Check lifecycle and regional compatibility."
  type        = string
}
variable "mq_instance_type" {
  type    = string
  default = "mq.m5.large"
}
variable "mq_admin_password" {
  description = "Only for hypothetical provisioning. Sensitive but stored in Terraform state by aws_mq_broker. Never put in tfvars or Git."
  type        = string
  sensitive   = true
  validation {
    condition     = length(var.mq_admin_password) >= 12 && length(var.mq_admin_password) <= 250 && !can(regex("[,:=]", var.mq_admin_password))
    error_message = "MQ password: 12-250 characters; no comma, colon or equals sign."
  }
}
variable "deploy_applications" {
  description = "False by default: no ECS task definitions/services. Infrastructure would still be created by apply."
  type        = bool
  default     = false
}
variable "application_adaptations_verified" {
  description = "Explicit statement that PostgreSQL/Cognito/Bedrock, secrets and migrations have been handled. Not evidence by itself."
  type        = bool
  default     = false
}
variable "container_images" {
  description = "ECR image URIs pinned by sha256 for backend, processor, azure-cost-api. No images are built or pushed by this template."
  type        = map(string)
  default     = {}
  validation {
    condition     = alltrue([for image in values(var.container_images) : can(regex("^[0-9]{12}\\.dkr\\.ecr\\.[a-z0-9-]+\\.amazonaws\\.com/[a-z0-9/_-]+@sha256:[a-f0-9]{64}$", image))])
    error_message = "Use private ECR image URIs pinned to a sha256 digest."
  }
}
variable "application_environment" {
  description = "Non-secret environment variables for adapted images; never credentials. Required Bedrock model/provider configuration belongs here after code adaptation."
  type        = map(map(string))
  default     = {}
}
variable "bedrock_model_arns" {
  description = "Exact foundation-model ARNs in this region; empty means no inference permissions. Cross-region profiles need a separate IAM review."
  type        = list(string)
  default     = []
  validation {
    condition     = alltrue([for arn in var.bedrock_model_arns : can(regex("^arn:aws:bedrock:${var.region}::foundation-model/[^*]+$", arn))])
    error_message = "Use exact regional foundation-model ARNs, without wildcard or cross-region profiles."
  }
}
variable "desired_count" {
  type    = number
  default = 2
  validation {
    condition     = var.desired_count >= 1 && floor(var.desired_count) == var.desired_count
    error_message = "desired_count must be a positive integer."
  }
}
variable "final_snapshot_suffix" {
  description = "Unique suffix chosen for a future deletion's final DB snapshots."
  type        = string
  default     = "retained"
}
