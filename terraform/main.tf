# ─── Docker Network ───────────────────────────────────────────────────────────
resource "docker_network" "sre_network" {
  name   = "sre-network"
  driver = "bridge"

  labels {
    label = "environment"
    value = var.environment
  }
  labels {
    label = "managed-by"
    value = "terraform"
  }
}

# ─── E-Commerce Application ───────────────────────────────────────────────────
resource "docker_image" "app" {
  name = var.app_image
  build {
    context    = "${path.module}/../app"
    dockerfile = "Dockerfile"
    tag        = ["ecommerce-app:latest"]
  }
  keep_locally = true
}

resource "docker_container" "app" {
  count = var.app_replicas
  name  = "ecommerce-app-${count.index}"
  image = docker_image.app.image_id

  networks_advanced {
    name = docker_network.sre_network.name
  }

  dynamic "ports" {
    for_each = count.index == 0 ? [1] : []
    content {
      internal = 5000
      external = var.app_port
    }
  }

  env = [
    "ENVIRONMENT=${var.environment}",
    "APP_REPLICA=${count.index}",
  ]

  healthcheck {
    test         = ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')"]
    interval     = "30s"
    timeout      = "5s"
    retries      = 3
    start_period = "15s"
  }

  restart = "unless-stopped"

  labels {
    label = "app"
    value = "ecommerce"
  }
  labels {
    label = "environment"
    value = var.environment
  }
}

# ─── Prometheus ───────────────────────────────────────────────────────────────
resource "docker_image" "prometheus" {
  name         = "prom/prometheus:v2.51.0"
  keep_locally = true
}

resource "docker_container" "prometheus" {
  name  = "prometheus"
  image = docker_image.prometheus.image_id

  networks_advanced {
    name = docker_network.sre_network.name
  }

  ports {
    internal = 9090
    external = var.prometheus_port
  }

  volumes {
    host_path      = abspath("${path.module}/../monitoring/prometheus")
    container_path = "/etc/prometheus"
    read_only      = true
  }

  command = [
    "--config.file=/etc/prometheus/prometheus.yml",
    "--storage.tsdb.path=/prometheus",
    "--storage.tsdb.retention.time=15d",
    "--web.enable-lifecycle",
  ]

  restart = "unless-stopped"
}

# ─── Alertmanager ─────────────────────────────────────────────────────────────
resource "docker_image" "alertmanager" {
  name         = "prom/alertmanager:v0.27.0"
  keep_locally = true
}

resource "docker_container" "alertmanager" {
  name  = "alertmanager"
  image = docker_image.alertmanager.image_id

  networks_advanced {
    name = docker_network.sre_network.name
  }

  ports {
    internal = 9093
    external = 9093
  }

  volumes {
    host_path      = abspath("${path.module}/../monitoring/alertmanager")
    container_path = "/etc/alertmanager"
    read_only      = true
  }

  restart = "unless-stopped"
}

# ─── Grafana ──────────────────────────────────────────────────────────────────
resource "docker_image" "grafana" {
  name         = "grafana/grafana:10.4.0"
  keep_locally = true
}

resource "docker_container" "grafana" {
  name  = "grafana"
  image = docker_image.grafana.image_id

  networks_advanced {
    name = docker_network.sre_network.name
  }

  ports {
    internal = 3000
    external = var.grafana_port
  }

  volumes {
    host_path      = abspath("${path.module}/../monitoring/grafana")
    container_path = "/etc/grafana/provisioning"
    read_only      = true
  }

  env = [
    "GF_SECURITY_ADMIN_PASSWORD=${var.grafana_admin_password}",
    "GF_USERS_ALLOW_SIGN_UP=false",
    "GF_ANALYTICS_REPORTING_ENABLED=false",
  ]

  restart = "unless-stopped"
}
