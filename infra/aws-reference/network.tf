resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true
  tags                 = { Name = local.name }
}
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id
}
resource "aws_subnet" "public" {
  for_each                = local.zones
  vpc_id                  = aws_vpc.main.id
  availability_zone       = each.key
  cidr_block              = cidrsubnet(var.vpc_cidr, 8, each.value)
  map_public_ip_on_launch = false
  tags                    = { Name = "${local.name}-egress-${each.key}" }
}
resource "aws_subnet" "app" {
  for_each          = local.zones
  vpc_id            = aws_vpc.main.id
  availability_zone = each.key
  cidr_block        = cidrsubnet(var.vpc_cidr, 8, each.value + 10)
  tags              = { Name = "${local.name}-app-${each.key}" }
}
resource "aws_subnet" "data" {
  for_each          = local.zones
  vpc_id            = aws_vpc.main.id
  availability_zone = each.key
  cidr_block        = cidrsubnet(var.vpc_cidr, 8, each.value + 20)
  tags              = { Name = "${local.name}-data-${each.key}" }
}
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id
}
resource "aws_route" "internet" {
  route_table_id         = aws_route_table.public.id
  destination_cidr_block = "0.0.0.0/0"
  gateway_id             = aws_internet_gateway.main.id
}
resource "aws_route_table_association" "public" {
  for_each       = local.zones
  subnet_id      = aws_subnet.public[each.key].id
  route_table_id = aws_route_table.public.id
}
locals {
  nat_zones = var.single_nat_gateway ? { (var.availability_zones[0]) = 0 } : local.zones
}
resource "aws_eip" "nat" {
  for_each = local.nat_zones
  domain   = "vpc"
}
resource "aws_nat_gateway" "main" {
  for_each      = local.nat_zones
  allocation_id = aws_eip.nat[each.key].id
  subnet_id     = aws_subnet.public[each.key].id
  depends_on    = [aws_internet_gateway.main]
}
resource "aws_route_table" "app" {
  for_each = local.zones
  vpc_id   = aws_vpc.main.id
}
resource "aws_route" "app_egress" {
  for_each               = local.zones
  route_table_id         = aws_route_table.app[each.key].id
  destination_cidr_block = "0.0.0.0/0"
  nat_gateway_id         = aws_nat_gateway.main[var.single_nat_gateway ? var.availability_zones[0] : each.key].id
}
resource "aws_route_table_association" "app" {
  for_each       = local.zones
  subnet_id      = aws_subnet.app[each.key].id
  route_table_id = aws_route_table.app[each.key].id
}
resource "aws_route_table" "data" {
  vpc_id = aws_vpc.main.id
}
resource "aws_route_table_association" "data" {
  for_each       = local.zones
  subnet_id      = aws_subnet.data[each.key].id
  route_table_id = aws_route_table.data.id
}
resource "aws_vpc_endpoint" "s3" {
  vpc_id            = aws_vpc.main.id
  service_name      = "com.amazonaws.${var.region}.s3"
  vpc_endpoint_type = "Gateway"
  route_table_ids   = [for table in aws_route_table.app : table.id]
}

resource "aws_security_group" "component" {
  for_each    = toset(["alb", "backend", "processor", "azure-cost-api", "db", "mq"])
  name_prefix = "${local.name}-${each.key}-"
  description = "Economicon ${each.key}: explicit rules only"
  vpc_id      = aws_vpc.main.id
}
data "aws_ec2_managed_prefix_list" "cloudfront" {
  name = "com.amazonaws.global.cloudfront.origin-facing"
}
resource "aws_vpc_security_group_ingress_rule" "edge_alb" {
  security_group_id = aws_security_group.component["alb"].id
  prefix_list_id    = data.aws_ec2_managed_prefix_list.cloudfront.id
  ip_protocol       = "tcp"
  from_port         = 443
  to_port           = 443
}
locals {
  connections = {
    alb_backend       = { source = "alb", target = "backend", port = 8000 }
    backend_db        = { source = "backend", target = "db", port = 5432 }
    processor_db      = { source = "processor", target = "db", port = 5432 }
    backend_mq        = { source = "backend", target = "mq", port = 5671 }
    processor_mq      = { source = "processor", target = "mq", port = 5671 }
    processor_fixture = { source = "processor", target = "azure-cost-api", port = 8002 }
  }
}
resource "aws_vpc_security_group_ingress_rule" "internal" {
  for_each                     = local.connections
  security_group_id            = aws_security_group.component[each.value.target].id
  referenced_security_group_id = aws_security_group.component[each.value.source].id
  ip_protocol                  = "tcp"
  from_port                    = each.value.port
  to_port                      = each.value.port
}
resource "aws_vpc_security_group_egress_rule" "internal" {
  for_each                     = local.connections
  security_group_id            = aws_security_group.component[each.value.source].id
  referenced_security_group_id = aws_security_group.component[each.value.target].id
  ip_protocol                  = "tcp"
  from_port                    = each.value.port
  to_port                      = each.value.port
}
resource "aws_vpc_security_group_egress_rule" "https" {
  for_each          = toset(["backend", "processor", "azure-cost-api"])
  security_group_id = aws_security_group.component[each.key].id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "tcp"
  from_port         = 443
  to_port           = 443
}
