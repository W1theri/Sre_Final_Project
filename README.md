# 🛒 E-Commerce SRE Capstone Project

> Production Readiness Review (PRR) — SRE Course Final Project

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    GitHub Actions CI/CD                  │
│  push → test → build image → push GHCR → deploy k8s    │
└─────────────────────────┬───────────────────────────────┘
                          │
          ┌───────────────▼────────────────┐
          │         Kubernetes Cluster      │
          │  ┌──────────┐  ┌──────────┐   │
          │  │  App-0   │  │  App-1   │   │  ← HPA (2–10 pods)
          │  │ :5000    │  │ :5000    │   │
          │  └────┬─────┘  └────┬─────┘   │
          └───────┼─────────────┼─────────┘
                  │             │
    ┌─────────────▼─────────────▼──────────┐
    │           Observability Stack         │
    │  Prometheus → Grafana Dashboard       │
    │  Alertmanager → Slack/Email           │
    └──────────────────────────────────────┘
```

## ⚡ Quick Start (Docker Compose — Recommended)

```bash
# 1. Clone the repository
git clone https://github.com/W1theri/ecommerce-sre-capstone.git
cd ecommerce-sre-capstone

# 2. Start everything
docker compose up -d --build

# 3. Check services
docker compose ps
```

**Access points:**
| Service       | URL                          | Credentials    |
|---------------|------------------------------|----------------|
| 🛒 API + tester | http://localhost:5000     | —              |
| 📊 Grafana     | http://localhost:3000         | admin / admin123 |
| 🔥 Prometheus  | http://localhost:9090         | —              |
| 🔔 Alertmanager | http://localhost:9093        | —              |

## 🌍 Terraform Deployment

```bash
cd terraform

# Initialize providers
terraform init

# Preview what will be created
terraform plan

# Apply infrastructure
terraform apply -auto-approve

# View outputs
terraform output
```

## ☸️ Kubernetes (Minikube)

```bash
# Start Minikube
minikube start --cpus=4 --memory=4096

# Enable metrics server (for HPA)
minikube addons enable metrics-server

# Apply manifests
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/hpa.yaml

# Watch HPA in action during load test
kubectl get hpa -n ecommerce --watch
```

## 🧪 API Testing

```bash
BASE=http://localhost:5000

# Browser API tester
# Open http://localhost:5000

# Health check
curl $BASE/health

# List products
curl $BASE/api/products

# Add to cart
curl -X POST $BASE/api/cart \
  -H 'Content-Type: application/json' \
  -d '{"product_id": 1, "quantity": 2}'

# Place order (use session_id from cart response)
curl -X POST $BASE/api/orders \
  -H 'Content-Type: application/json' \
  -d '{"session_id": "YOUR_SESSION_ID"}'
```

## 📈 Load Testing (Locust)

```bash
pip install locust

# Web UI mode (open http://localhost:8089)
locust -f tests/locustfile.py --host=http://localhost:5000

# Headless — 100 users, ramp 10/s, run 5 minutes
locust -f tests/locustfile.py \
  --host=http://localhost:5000 \
  --headless -u 100 -r 10 -t 5m \
  --html=load-test-report.html
```

## 📊 SLOs

| SLO | Target | Current |
|-----|--------|---------|
| Availability | ≥ 99.9% | See Grafana |
| p99 Latency | < 500ms | See Grafana |
| Error Rate | < 1% | See Grafana |
| Order Success | > 95% | See Grafana |

## 🗂 Project Structure

```
ecommerce-sre/
├── app/                    # Flask e-commerce API
│   ├── app.py              # Application code + Prometheus metrics
│   ├── Dockerfile          # Container definition
│   └── requirements.txt
├── terraform/              # Infrastructure as Code
│   ├── providers.tf        # Docker provider
│   ├── variables.tf        # Input variables
│   ├── main.tf             # Resources (containers, network)
│   └── outputs.tf          # Output values
├── k8s/                    # Kubernetes manifests
│   ├── namespace.yaml
│   ├── deployment.yaml     # App deployment
│   ├── service.yaml        # ClusterIP + NodePort
│   └── hpa.yaml            # Horizontal Pod Autoscaler
├── monitoring/
│   ├── prometheus/
│   │   ├── prometheus.yml  # Scrape configs
│   │   └── alerts.yml      # Alerting rules
│   ├── alertmanager/
│   │   └── alertmanager.yml
│   └── grafana/
│       ├── datasources/    # Prometheus datasource
│       └── dashboards/     # Pre-built SRE dashboard
├── tests/
│   └── locustfile.py       # Load testing scenarios
├── slo/
│   └── slo-definitions.md  # SLI/SLO documentation
├── .github/workflows/
│   └── ci-cd.yml           # GitHub Actions pipeline
└── docker-compose.yml      # Local dev stack
```

## 👥 Team

| Role | Responsibility |
|------|---------------|
| SRE Lead | Architecture, SLOs, Incident response |
| Infrastructure Engineer | Terraform, Kubernetes, CI/CD |
| Observability Engineer | Prometheus, Grafana, Alertmanager |
| Reliability Engineer | Load testing, Capacity planning |
