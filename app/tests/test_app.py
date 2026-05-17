import pytest

from app import app


@pytest.fixture()
def client():
    app.config.update(TESTING=True)
    with app.test_client() as test_client:
        yield test_client


def test_health_endpoint(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json()["status"] == "healthy"


def test_products_endpoint(client):
    response = client.get("/api/products")
    payload = response.get_json()

    assert response.status_code == 200
    assert payload["total"] >= 1
    assert payload["products"][0]["id"] == 1


def test_cart_and_order_flow(client, monkeypatch):
    monkeypatch.setattr("app.random.random", lambda: 0.99)

    cart_response = client.post(
        "/api/cart",
        json={"product_id": 1, "quantity": 2},
    )
    cart_payload = cart_response.get_json()

    assert cart_response.status_code == 201
    assert cart_payload["session_id"]
    assert len(cart_payload["cart"]) == 1

    order_response = client.post(
        "/api/orders",
        json={"session_id": cart_payload["session_id"]},
    )
    order_payload = order_response.get_json()

    assert order_response.status_code == 201
    assert order_payload["status"] == "confirmed"
    assert order_payload["total"] == 2599.98


def test_missing_product_returns_404(client):
    response = client.get("/api/products/999")

    assert response.status_code == 404
