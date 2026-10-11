terraform {
  required_version = ">= 1.13.3, < 2.0.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "6.13.0"
    }
  }
  # Local state for this unexecuted reference. See backend.s3.hcl.example.
}

provider "aws" {
  region = var.region
  default_tags {
    tags = local.tags
  }
}

provider "aws" {
  alias  = "edge"
  region = "us-east-1"
  default_tags {
    tags = local.tags
  }
}

locals {
  name = "${var.project}-${var.environment}"
  tags = {
    Project     = var.project
    Environment = var.environment
    ManagedBy   = "Terraform"
    Task        = "JUP-060"
  }
  zones = { for index, zone in var.availability_zones : zone => index }
}
