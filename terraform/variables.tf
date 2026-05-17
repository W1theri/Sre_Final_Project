variable "app_image" {
  description = "Docker image for the e-commerce application"
  type        = string
  default     = "ecommerce-app:latest"
}

variable "app_replicas" {
  description = "Number of app container replicas"
  type        = number
  default     = 2
}

variable "app_port" {
  description = "Host port to expose the application"
  type        = number
  default     = 5000
}

variable "prometheus_port" {
  description = "Host port for Prometheus"
  type        = number
  default     = 9090
}

variable "grafana_port" {
  description = "Host port for Grafana"
  type        = number
  default     = 3000
}

variable "grafana_admin_password" {
  description = "Grafana admin password"
  type        = string
  default     = "admin123"
  sensitive   = true
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "production"
  validation {
    condition     = contains(["development", "staging", "production"], var.environment)
    error_message = "Environment must be development, staging, or production."
  }
}
