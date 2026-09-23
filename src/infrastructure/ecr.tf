# ECR stores immutable container images used by the prediction Lambda.
resource "aws_ecr_repository" "prediction" {
  name                 = "${local.name_prefix}-prediction"
  image_tag_mutability = "IMMUTABLE"
  force_delete         = true

  encryption_configuration {
    encryption_type = "AES256"
  }

  image_scanning_configuration {
    scan_on_push = true
  }
}

resource "aws_ecr_lifecycle_policy" "prediction" {
  repository = aws_ecr_repository.prediction.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep the three most recent prediction images"
        selection = {
          tagStatus   = "any"
          countType   = "imageCountMoreThan"
          countNumber = 3
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}
