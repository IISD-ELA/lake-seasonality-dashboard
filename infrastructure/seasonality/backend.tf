terraform {
  backend "s3" {
    bucket         = "terraform-state-iisd-ela"
    key            = "lake-seasonality-dashboard/terraform.tfstate"
    region         = "ca-central-1"
    profile        = "iisd"
    dynamodb_table = "terraform-state-iisd-ela"
    encrypt        = true
  }
}
