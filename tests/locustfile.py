"""
E-Commerce Load Test — Locust
Usage:
    locust -f locustfile.py --host=http://localhost:5000
    locust -f locustfile.py --host=http://localhost:5000 --headless -u 100 -r 10 -t 5m
"""
from locust import HttpUser, task, between, events
import random
import json

# ─── Helper Data ─────────────────────────────────────────────────────────────
PRODUCT_IDS = [1, 2, 3, 4, 5]


class EcommerceUser(HttpUser):
    """Simulates a typical e-commerce user journey."""
    wait_time = between(1, 3)   # Think time between requests

    def on_start(self):
        """Called when a user starts — initialize session."""
        self.session_id = None
        self.browse_products()

    # ── Tasks with weights (higher = more frequent) ──────────────────────────

    @task(5)
    def browse_products(self):
        """Browse product catalog — most common action."""
        with self.client.get(
            "/api/products",
            name="/api/products",
            catch_response=True
        ) as resp:
            if resp.status_code == 200:
                resp.success()
            else:
                resp.failure(f"Got {resp.status_code}")

    @task(3)
    def view_product(self):
        """View a specific product."""
        product_id = random.choice(PRODUCT_IDS)
        with self.client.get(
            f"/api/products/{product_id}",
            name="/api/products/[id]",
            catch_response=True
        ) as resp:
            if resp.status_code == 200:
                resp.success()
            elif resp.status_code == 404:
                resp.failure("Product not found")
            else:
                resp.failure(f"Got {resp.status_code}")

    @task(2)
    def add_to_cart(self):
        """Add item to cart."""
        payload = {
            "product_id": random.choice(PRODUCT_IDS),
            "quantity":   random.randint(1, 3),
        }
        if self.session_id:
            payload["session_id"] = self.session_id
        with self.client.post(
            "/api/cart",
            json=payload,
            name="/api/cart (add)",
            catch_response=True
        ) as resp:
            if resp.status_code == 201:
                data = resp.json()
                self.session_id = data.get("session_id")
                resp.success()
            else:
                resp.failure(f"Got {resp.status_code}")

    @task(1)
    def checkout(self):
        """Complete an order — least frequent but most important."""
        if not self.session_id:
            return

        with self.client.post(
            "/api/orders",
            json={"session_id": self.session_id},
            name="/api/orders (checkout)",
            catch_response=True
        ) as resp:
            if resp.status_code == 201:
                self.session_id = None   # Reset cart after order
                resp.success()
            elif resp.status_code == 400:
                resp.failure("Empty cart")
            elif resp.status_code == 500:
                resp.failure("Payment failed (expected ~5%)")
            else:
                resp.failure(f"Got {resp.status_code}")

    @task(1)
    def health_check(self):
        """Simulate monitoring health checks."""
        self.client.get("/health", name="/health")


class SpikeUser(HttpUser):
    """Aggressive user for spike testing."""
    wait_time = between(0.1, 0.5)

    @task
    def hammer_products(self):
        self.client.get("/api/products", name="/api/products [spike]")


# ─── Event Hooks ─────────────────────────────────────────────────────────────
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    print("🚀 Load test starting...")
    print(f"   Target: {environment.host}")

@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    stats = environment.stats.total
    print("\n📊 Load Test Summary:")
    print(f"   Total requests:  {stats.num_requests}")
    print(f"   Failed requests: {stats.num_failures}")
    print(f"   Avg response:    {stats.avg_response_time:.0f}ms")
    print(f"   RPS:             {stats.current_rps:.1f}")
    error_rate = (stats.num_failures / stats.num_requests * 100) if stats.num_requests else 0
    print(f"   Error rate:      {error_rate:.2f}%")
    if error_rate < 1.0:
        print("   ✅ SLO MET: Error rate < 1%")
    else:
        print("   ❌ SLO BREACH: Error rate >= 1%")
