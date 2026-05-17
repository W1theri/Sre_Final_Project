output "app_url" {
  description = "E-Commerce API URL"
  value       = "http://localhost:${var.app_port}"
}

output "prometheus_url" {
  description = "Prometheus URL"
  value       = "http://localhost:${var.prometheus_port}"
}

output "grafana_url" {
  description = "Grafana Dashboard URL"
  value       = "http://localhost:${var.grafana_port}"
}

output "alertmanager_url" {
  description = "Alertmanager URL"
  value       = "http://localhost:9093"
}

output "network_name" {
  description = "Docker network name"
  value       = docker_network.sre_network.name
}

output "app_container_names" {
  description = "App container names"
  value       = [for c in docker_container.app : c.name]
}
