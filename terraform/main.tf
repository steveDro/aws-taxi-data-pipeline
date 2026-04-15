
# ──────────────────────────────────────────
# IAM User
# ──────────────────────────────────────────
resource "aws_iam_user" "data_engineer_user" {
  name = "data-engineer-user"
  path = "/system/"

  tags = {
    Environment = "Dev"
    Project     = "taxi-data-pipeline"
  }
}

resource "aws_iam_access_key" "data_engineer_user" {
  user = aws_iam_user.data_engineer_user.name
}

output "access_key_id" {
  value     = aws_iam_access_key.data_engineer_user.id
  sensitive = true
}

output "secret_access_key" {
  value     = aws_iam_access_key.data_engineer_user.secret
  sensitive = true
}

# ──────────────────────────────────────────
# S3 Bucket
# ──────────────────────────────────────────
resource "aws_s3_bucket" "taxi_pipeline" {
  bucket = "stv-taxi-data-pipeline"

  tags = {
    Name        = "taxi-data-pipeline"
    Environment = "Dev"
    Project     = "taxi-data-pipeline"
  }
}

resource "aws_s3_bucket_versioning" "taxi_pipeline" {
  bucket = aws_s3_bucket.taxi_pipeline.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "taxi_pipeline" {
  bucket = aws_s3_bucket.taxi_pipeline.id

  rule {
    id     = "expire-raw-data"
    status = "Enabled"

    filter {
      prefix = "raw/"
    }

    expiration {
      days = 90
    }
  }
}

# ──────────────────────────────────────────
# IAM Policy — scoped to pipeline bucket only
# ──────────────────────────────────────────
data "aws_iam_policy_document" "taxi_pipeline_s3" {
  statement {
    sid    = "AllowBucketAccess"
    effect = "Allow"

    actions = [
      "s3:ListBucket",
      "s3:GetBucketLocation"
    ]

    resources = [
      aws_s3_bucket.taxi_pipeline.arn
    ]
  }

  statement {
    sid    = "AllowObjectAccess"
    effect = "Allow"

    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:DeleteObject"
    ]

    resources = [
      "${aws_s3_bucket.taxi_pipeline.arn}/*"
    ]
  }
}

resource "aws_iam_policy" "taxi_pipeline_s3" {
  name        = "taxi-pipeline-s3-policy"
  path        = "/"
  description = "Scoped S3 access for the taxi data pipeline"
  policy      = data.aws_iam_policy_document.taxi_pipeline_s3.json
}

resource "aws_iam_user_policy_attachment" "data_engineer_user_s3" {
  user       = aws_iam_user.data_engineer_user.name
  policy_arn = aws_iam_policy.taxi_pipeline_s3.arn
}

# ──────────────────────────────────────────
# IAM Role — allows Redshift to access S3
# ──────────────────────────────────────────
resource "aws_iam_role" "redshift_s3_role" {
  name = "redshift-s3-access-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "redshift.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })

  tags = {
    Environment = "Dev"
    Project     = "taxi-data-pipeline"
  }
}

resource "aws_iam_role_policy_attachment" "redshift_s3" {
  role       = aws_iam_role.redshift_s3_role.name
  policy_arn = aws_iam_policy.taxi_pipeline_s3.arn
}

# ──────────────────────────────────────────
# Networking — VPC, Subnet, Security Group
# ──────────────────────────────────────────
resource "aws_vpc" "taxi_pipeline" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true

  tags = {
    Name    = "taxi-pipeline-vpc"
    Project = "taxi-data-pipeline"
  }
}

resource "aws_subnet" "redshift" {
  vpc_id            = aws_vpc.taxi_pipeline.id
  cidr_block        = "10.0.1.0/24"
  availability_zone = "us-east-1a"

  tags = {
    Name    = "taxi-pipeline-redshift-subnet"
    Project = "taxi-data-pipeline"
  }
}

resource "aws_security_group" "redshift" {
  name        = "redshift-sg"
  description = "Allow Redshift inbound traffic"
  vpc_id      = aws_vpc.taxi_pipeline.id

  ingress {
    description = "Redshift port"
    from_port   = 5439
    to_port     = 5439
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # restrict to your IP in production
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name    = "taxi-pipeline-redshift-sg"
    Project = "taxi-data-pipeline"
  }
}

resource "aws_redshift_subnet_group" "taxi_pipeline" {
  name       = "taxi-pipeline-subnet-group"
  subnet_ids = [aws_subnet.redshift.id]

  tags = {
    Name    = "taxi-pipeline-subnet-group"
    Project = "taxi-data-pipeline"
  }
}

# ──────────────────────────────────────────
# Redshift Provisioned Cluster
# ──────────────────────────────────────────
resource "aws_redshift_cluster" "taxi_pipeline" {
  cluster_identifier        = "taxi-pipeline-cluster"
  database_name             = "taxi_db"
  master_username           = var.redshift_username
  master_password           = var.redshift_password
  node_type                 = "ra3.xlplus"
  cluster_type              = "multi-node"
  number_of_nodes           = 2
  vpc_security_group_ids    = [aws_security_group.redshift.id]
  cluster_subnet_group_name = aws_redshift_subnet_group.taxi_pipeline.name
  iam_roles                 = [aws_iam_role.redshift_s3_role.arn]
  skip_final_snapshot       = true
  publicly_accessible       = true # set to false in production

  tags = {
    Name        = "taxi-pipeline-cluster"
    Environment = "Dev"
    Project     = "taxi-data-pipeline"
  }
}

# ──────────────────────────────────────────
# Internet Gateway
# ──────────────────────────────────────────
resource "aws_internet_gateway" "taxi_pipeline" {
  vpc_id = aws_vpc.taxi_pipeline.id

  tags = {
    Name    = "taxi-pipeline-igw"
    Project = "taxi-data-pipeline"
  }
}

# ──────────────────────────────────────────
# Route Table — directs traffic to the IGW
# ──────────────────────────────────────────
resource "aws_route_table" "taxi_pipeline" {
  vpc_id = aws_vpc.taxi_pipeline.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.taxi_pipeline.id
  }

  tags = {
    Name    = "taxi-pipeline-rt"
    Project = "taxi-data-pipeline"
  }
}

resource "aws_route_table_association" "redshift" {
  subnet_id      = aws_subnet.redshift.id
  route_table_id = aws_route_table.taxi_pipeline.id
}

# ──────────────────────────────────────────
# Outputs
# ──────────────────────────────────────────
output "redshift_endpoint" {
  description = "Redshift cluster endpoint"
  value       = aws_redshift_cluster.taxi_pipeline.endpoint
}

output "redshift_role_arn" {
  description = "IAM role ARN for Redshift to access S3 (use in COPY commands)"
  value       = aws_iam_role.redshift_s3_role.arn
}
