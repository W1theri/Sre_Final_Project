terraform {
  required_version = ">= 1.5.0"

  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
  }

  # Local state (for production use remote backend like S3/GCS)
  backend "local" {
    path = "terraform.tfstate"
  }
}

provider "docker" {
  host = var.docker_host
}
