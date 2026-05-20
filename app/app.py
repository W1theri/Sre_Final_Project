from flask import Flask, jsonify, request, abort
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
import time
import random
import uuid

app = Flask(__name__)

# ─── Prometheus Metrics ───────────────────────────────────────────────────────
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)
REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['endpoint'],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]
)
ACTIVE_USERS = Gauge('active_users_total', 'Currently active users')
ORDERS_TOTAL = Counter('orders_total', 'Total orders placed', ['status'])
CART_SIZE = Histogram('cart_items_total', 'Number of items in cart', buckets=[1,2,3,5,10,20])

# ─── In-memory "Database" ─────────────────────────────────────────────────────
PRODUCTS = [
    {"id": 1, "name": "Laptop Pro X",     "price": 1299.99, "stock": 50},
    {"id": 2, "name": "Wireless Mouse",   "price": 29.99,   "stock": 200},
    {"id": 3, "name": "Mechanical KB",    "price": 89.99,   "stock": 75},
    {"id": 4, "name": "4K Monitor",       "price": 499.99,  "stock": 30},
    {"id": 5, "name": "USB-C Hub",        "price": 49.99,   "stock": 150},
]

ORDERS = {}
CARTS  = {}

# ─── Middleware ───────────────────────────────────────────────────────────────
@app.before_request
def start_timer():
    request._start_time = time.time()

@app.after_request
def record_metrics(response):
    latency = time.time() - getattr(request, '_start_time', time.time())
    endpoint = request.url_rule.rule if request.url_rule else request.path
    REQUEST_COUNT.labels(request.method, endpoint, response.status_code).inc()
    REQUEST_LATENCY.labels(endpoint).observe(latency)
    return response

# ─── Routes ───────────────────────────────────────────────────────────────────
@app.route('/health')
def health():
    return jsonify({"status": "healthy", "service": "ecommerce-api", "version": "1.0.0"})

@app.route('/')
def frontend():
    return app.send_static_file('index.html')

@app.route('/metrics')
def metrics():
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

@app.route('/api/products', methods=['GET'])
def list_products():
    category = request.args.get('category')
    result = PRODUCTS
    return jsonify({"products": result, "total": len(result)})

@app.route('/api/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    product = next((p for p in PRODUCTS if p['id'] == product_id), None)
    if not product:
        abort(404)
    return jsonify(product)

@app.route('/api/cart', methods=['POST'])
def add_to_cart():
    data = request.get_json()
    if not data or 'product_id' not in data or 'quantity' not in data:
        abort(400)

    product = next((p for p in PRODUCTS if p['id'] == data['product_id']), None)
    if not product:
        abort(404)

    session_id = data.get('session_id', str(uuid.uuid4()))
    if session_id not in CARTS:
        CARTS[session_id] = []

    CARTS[session_id].append({
        "product_id": data['product_id'],
        "name": product['name'],
        "price": product['price'],
        "quantity": data['quantity']
    })

    CART_SIZE.observe(len(CARTS[session_id]))
    ACTIVE_USERS.set(len(CARTS))

    return jsonify({"session_id": session_id, "cart": CARTS[session_id]}), 201

@app.route('/api/cart/<session_id>', methods=['GET'])
def get_cart(session_id):
    cart = CARTS.get(session_id, [])
    total = sum(item['price'] * item['quantity'] for item in cart)
    return jsonify({"session_id": session_id, "items": cart, "total": round(total, 2)})

@app.route('/api/orders', methods=['POST'])
def place_order():
    data = request.get_json()
    if not data or 'session_id' not in data:
        abort(400)

    session_id = data['session_id']
    cart = CARTS.get(session_id, [])
    if not cart:
        abort(400)

    # Simulate occasional failures (5% error rate for realism)
    if random.random() < 0.05:
        ORDERS_TOTAL.labels('failed').inc()
        return jsonify({"error": "Payment processing failed"}), 500

    order_id = str(uuid.uuid4())
    total = sum(item['price'] * item['quantity'] for item in cart)

    ORDERS[order_id] = {
        "order_id": order_id,
        "session_id": session_id,
        "items": cart,
        "total": round(total, 2),
        "status": "confirmed"
    }

    del CARTS[session_id]
    ACTIVE_USERS.set(len(CARTS))
    ORDERS_TOTAL.labels('success').inc()

    return jsonify(ORDERS[order_id]), 201

@app.route('/api/orders/<order_id>', methods=['GET'])
def get_order(order_id):
    order = ORDERS.get(order_id)
    if not order:
        abort(404)
    return jsonify(order)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
