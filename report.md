# E-Commerce SRE Capstone Technical Report

## 1. Executive Summary

This project implements a small e-commerce API with production-readiness practices around infrastructure provisioning, CI/CD, observability, alerting, SLOs, autoscaling, and load testing.

The application is a Flask service exposing product, cart, order, health, metrics, and browser API testing endpoints. The reliability stack includes Terraform-managed local infrastructure, Docker Compose for local operation, Kubernetes manifests for cluster deployment, Prometheus metrics scraping, Grafana dashboards, Alertmanager routing, Horizontal Pod Autoscaling, and Locust load tests.

## 2. Requirements Coverage

| Requirement | Status | Evidence |
|---|---:|---|
| Use Terraform to provision infrastructure | Met | `terraform/main.tf`, `terraform/providers.tf`, `terraform/variables.tf`, `terraform/outputs.tf` |
| Infrastructure reproducible from scratch | Met | Terraform provisions Docker network, app replicas, Prometheus, Grafana, and Alertmanager; Docker Compose also provides a local stack |
| Proper Terraform variables and state | Mostly met | Variables are defined in `terraform/variables.tf`; local backend is configured in `terraform/providers.tf`. For production, a remote backend should replace local state |
| CI/CD pipeline configured | Met | `.github/workflows/ci-cd.yml` |
| Automatically build Docker images | Met | GitHub Actions uses `docker/build-push-action@v5` |
| Push images to registry | Met | Images are pushed to GitHub Container Registry, `ghcr.io` |
| Automatically deploy updates to cluster | Partially met | Deploy job updates Kubernetes deployment using `kubectl`; requires a valid base64 `KUBECONFIG` GitHub secret for a reachable remote cluster |
| Deploy Prometheus and Grafana | Met | `docker-compose.yml` and Terraform define Prometheus and Grafana services |
| Configure metrics scraping | Met | `monitoring/prometheus/prometheus.yml` scrapes app replicas, Prometheus, and node-exporter |
| Create Grafana dashboards visualizing SLIs | Met | `monitoring/grafana/dashboards/ecommerce-sre.json` and provisioning files |
| Configure Alertmanager rules | Met | Prometheus alert rules in `monitoring/prometheus/alerts.yml`; routing in `monitoring/alertmanager/alertmanager.yml` |
| Define SLIs and SLOs | Met | `slo/slo-definitions.md` |
| Configure autoscaling policies | Met | `k8s/hpa.yaml` scales 2 to 10 pods on CPU and memory |
| Perform load testing | Met | `tests/locustfile.py` defines normal and spike traffic scenarios |

## 3. Architecture

### Application

The core service is a Flask API in `app/app.py`. It exposes:

| Endpoint | Purpose |
|---|---|
| `/` | Browser API testing frontend |
| `/health` | Health check endpoint |
| `/metrics` | Prometheus metrics endpoint |
| `/api/products` | Product catalog listing |
| `/api/products/<id>` | Single product lookup |
| `/api/cart` | Add product to cart |
| `/api/cart/<session_id>` | Retrieve cart |
| `/api/orders` | Place order |
| `/api/orders/<order_id>` | Retrieve order |

The service stores product, cart, and order data in memory for demo purposes. Prometheus metrics are emitted through `prometheus-client`.

### Runtime Topology

```text
Developer / GitHub Actions
        |
        v
GitHub Actions CI/CD
  - run tests
  - build Docker image
  - push to GHCR
  - deploy to Kubernetes with kubectl
        |
        v
Kubernetes namespace: ecommerce
  - Deployment: ecommerce-app
  - Service: ecommerce-service
  - NodePort: ecommerce-nodeport
  - HPA: ecommerce-hpa
        |
        v
Observability stack
  - Prometheus scrapes /metrics
  - Grafana visualizes SLIs
  - Alertmanager routes alerts
```

### Local Stack

For local execution, `docker-compose.yml` starts:

| Service | Port | Purpose |
|---|---:|---|
| ecommerce-app-0 | 5000 | API and browser tester |
| ecommerce-app-1 | internal | second API replica for Prometheus scraping |
| Prometheus | 9090 | metrics storage and alert evaluation |
| Grafana | 3000 | dashboard visualization |
| Alertmanager | 9093 | alert routing |
| node-exporter | 9100 | host/system metrics |

## 4. Infrastructure as Code

Terraform configuration is stored under `terraform/`.

Implemented resources:

| File | Purpose |
|---|---|
| `providers.tf` | Terraform version, Docker provider, local state backend |
| `variables.tf` | App image, replica count, exposed ports, Grafana password, environment |
| `main.tf` | Docker network, app containers, Prometheus, Grafana, Alertmanager |
| `outputs.tf` | URLs and container/network outputs |

The infrastructure is reproducible from scratch with:

```bash
cd terraform
terraform init
terraform plan
terraform apply
```

State is currently local at `terraform/terraform.tfstate`. For a real production deployment, this should be moved to a remote backend such as S3, GCS, Azure Storage, Terraform Cloud, or another shared state store with locking.

## 5. CI/CD Pipeline

The pipeline is defined in `.github/workflows/ci-cd.yml`.

### Job 1: Run Tests

Runs on pull requests and pushes. It installs Python dependencies and executes unit tests with coverage:

```bash
cd app
python -m pytest tests/ -v --cov=app --cov-report=xml
```

### Job 2: Build & Push Image

Builds the Docker image from `./app`, pushes tags to GitHub Container Registry, and scans the pushed image with Trivy.

The workflow uses `docker/metadata-action` to generate valid image tags and passes the selected image reference to later jobs.

### Job 3: Deploy to Cluster

Deploys only on pushes to `main`.

The job:

1. Installs `kubectl`.
2. Decodes the base64 `KUBECONFIG` repository secret.
3. Verifies cluster access with `kubectl config current-context` and `kubectl cluster-info`.
4. Updates the `ecommerce-app` Kubernetes deployment image.
5. Waits for rollout completion.
6. Verifies pods.
7. Rolls back only if kubeconfig setup succeeded.

Important note: GitHub-hosted runners cannot deploy to local Minikube unless it is exposed through a reachable network path. A valid remote cluster kubeconfig must be stored in the GitHub secret `KUBECONFIG`.

## 6. Observability and Alerting

### Metrics

The app exposes Prometheus metrics at `/metrics`.

Custom metrics include:

| Metric | Type | Purpose |
|---|---|---|
| `http_requests_total` | Counter | HTTP request count by method, endpoint, and status |
| `http_request_duration_seconds` | Histogram | HTTP request latency by endpoint |
| `active_users_total` | Gauge | Active cart sessions |
| `orders_total` | Counter | Order outcomes by status |
| `cart_items_total` | Histogram | Cart size distribution |

### Prometheus

Prometheus config is in `monitoring/prometheus/prometheus.yml`.

Scrape targets:

| Job | Targets |
|---|---|
| `ecommerce-app` | `ecommerce-app-0:5000`, `ecommerce-app-1:5000` |
| `prometheus` | `localhost:9090` |
| `node-exporter` | `node-exporter:9100` |

### Grafana

Grafana provisioning is configured in:

| File | Purpose |
|---|---|
| `monitoring/grafana/datasources/datasource.yml` | Prometheus datasource |
| `monitoring/grafana/dashboards/dashboard.yml` | Dashboard provider |
| `monitoring/grafana/dashboards/ecommerce-sre.json` | SRE dashboard |

### Alerting

Prometheus alert rules are in `monitoring/prometheus/alerts.yml`.

Configured alerts:

| Alert | Condition | Severity |
|---|---|---|
| `HighErrorRate` | 5xx rate > 1% over 5 minutes | warning |
| `CriticalErrorRate` | 5xx rate > 5% over 5 minutes | critical |
| `HighLatencyP99` | p99 latency > 500ms | warning |
| `CriticalLatencyP99` | p99 latency > 1s | critical |
| `ServiceDown` | app scrape target is down | critical |
| `NoTraffic` | no requests for 5 minutes | warning |
| `HighOrderFailureRate` | order failure rate > 10% | warning |

Alertmanager routing is configured in `monitoring/alertmanager/alertmanager.yml`, with receivers for default, critical, and SRE team alerts. Webhook endpoints are placeholders for local/demo routing; Slack/email configs are documented as comments for real integration.

## 7. SLOs and SLIs

SLO definitions are documented in `slo/slo-definitions.md`.

| SLO | Target | Measurement |
|---|---|---|
| Availability | 99.9% over rolling 30 days | Successful non-5xx requests / total requests |
| p99 latency | < 500ms | Prometheus histogram quantile |
| p95 latency | < 200ms | Prometheus histogram quantile |
| Error rate | < 1% over 5 minutes | 5xx responses / total responses |
| Order success rate | > 95% | Successful orders / all order attempts |

Error budget policy is included in the SLO document, ranging from normal development when budget is healthy to deployment freeze when budget is exhausted.

## 8. Scaling Strategy

Kubernetes scaling is defined in `k8s/hpa.yaml`.

The Horizontal Pod Autoscaler configuration:

| Setting | Value |
|---|---:|
| Target deployment | `ecommerce-app` |
| Minimum replicas | 2 |
| Maximum replicas | 10 |
| CPU target | 60% utilization |
| Memory target | 70% utilization |
| Scale-up stabilization | 30 seconds |
| Scale-up policy | add up to 3 pods per 60 seconds |
| Scale-down stabilization | 300 seconds |
| Scale-down policy | remove 1 pod per 120 seconds |

This strategy reacts quickly to traffic spikes while slowing down scale-in to avoid oscillation.

The deployment also defines CPU and memory requests/limits in `k8s/deployment.yaml`, which are required for resource-based HPA decisions.

## 9. Load Testing

Load testing is implemented with Locust in `tests/locustfile.py`.

Scenarios:

| User class | Purpose |
|---|---|
| `EcommerceUser` | realistic product browsing, cart, checkout, and health check traffic |
| `SpikeUser` | aggressive product endpoint traffic for spike testing |

Example commands:

```bash
locust -f tests/locustfile.py --host=http://localhost:5000
```

```bash
locust -f tests/locustfile.py --host=http://localhost:5000 --headless -u 100 -r 10 -t 5m --html=load-test-report.html
```

During Kubernetes testing, scaling can be observed with:

```bash
kubectl get hpa -n ecommerce --watch
kubectl get pods -n ecommerce -w
```

## 10. Screenshot Placeholders

Replace these placeholders with actual screenshots before submission.

### CI/CD Successful Execution

![GitHub Actions successful pipeline screenshot](screenshots/github-actions-success.png)

Expected evidence:

- Job 1: Run Tests passed
- Job 2: Build & Push Image passed
- Job 3: Deploy to Cluster passed, or documented as skipped if no reachable remote cluster is available

### Docker Image Registry

![GHCR image package screenshot](screenshots/ghcr-image-package.png)

Expected evidence:

- `ecommerce-app` image exists in GitHub Container Registry
- Recent image tag from the workflow is visible

### Grafana SLI Dashboard

![Grafana SRE dashboard screenshot](screenshots/grafana-sli-dashboard.png)

Expected evidence:

- request rate
- p95/p99 latency
- error rate
- service health
- order success/failure metrics

### Prometheus Targets

![Prometheus targets screenshot](screenshots/prometheus-targets.png)

Expected evidence:

- `ecommerce-app` targets are UP
- `prometheus` target is UP
- `node-exporter` target is UP

### Alertmanager Alerts

![Alertmanager alerts screenshot](screenshots/alertmanager-alerts.png)

Expected evidence:

- alert route configuration visible
- firing or resolved alert example if available

### Kubernetes HPA Before Load

![Kubernetes HPA before load screenshot](screenshots/hpa-before-load.png)

Expected evidence:

- HPA minimum replicas at 2
- CPU/memory utilization below target

### Kubernetes HPA During Traffic Spike

![Kubernetes HPA during load screenshot](screenshots/hpa-during-load.png)

Expected evidence:

- replicas increasing above 2
- CPU or memory target exceeded
- pods scaling out during Locust traffic

### Locust Load Test

![Locust load test screenshot](screenshots/locust-load-test.png)

Expected evidence:

- active users
- requests per second
- response time statistics
- failure percentage

## 11. Known Limitations and Recommendations

1. Terraform uses local state. For team or production usage, configure a remote backend with state locking.
2. GitHub Actions deployment requires a reachable Kubernetes cluster and a valid base64 `KUBECONFIG` secret.
3. Local Minikube cannot be reached directly from GitHub-hosted runners.
4. Alertmanager webhook URLs are placeholders. Configure real Slack, email, or incident-management receivers for production.
5. The demo application uses in-memory data, so carts and orders are not persistent across restarts.
6. The app simulates a 5% order failure rate. This is useful for alert testing, but should be disabled or controlled by configuration for production.

## 12. Conclusion

The project meets the main SRE capstone requirements for infrastructure as code, CI/CD, observability, alerting, SLO definition, autoscaling, and load testing. The remaining work before final submission is primarily evidence collection: add screenshots for successful pipeline execution, Grafana dashboards, alerting, Prometheus targets, Locust results, and Kubernetes HPA scaling under load.
