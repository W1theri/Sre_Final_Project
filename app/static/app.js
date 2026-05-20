const healthDot = document.querySelector("#health-dot");
const healthText = document.querySelector("#health-text");
const productsEl = document.querySelector("#products");
const productSelect = document.querySelector("#product-id");
const responseLog = document.querySelector("#response-log");
const sessionInput = document.querySelector("#session-id");
const cartSummary = document.querySelector("#cart-summary");

let products = [];

function writeLog(label, data) {
  responseLog.textContent = JSON.stringify({ label, data }, null, 2);
}

async function request(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  const text = await response.text();
  const payload = text ? JSON.parse(text) : null;

  if (!response.ok) {
    const error = new Error(`HTTP ${response.status}`);
    error.payload = payload;
    throw error;
  }

  return payload;
}

function renderProducts() {
  productSelect.innerHTML = products
    .map((product) => `<option value="${product.id}">${product.name} - $${product.price}</option>`)
    .join("");

  productsEl.innerHTML = products
    .map((product) => `
      <article class="product">
        <h3>${product.name}</h3>
        <p>ID: ${product.id}</p>
        <p>Price: $${product.price}</p>
        <p>Stock: ${product.stock}</p>
      </article>
    `)
    .join("");
}

function renderCart(cart) {
  if (!cart.items || cart.items.length === 0) {
    cartSummary.textContent = "Cart is empty.";
    return;
  }

  const itemCount = cart.items.reduce((sum, item) => sum + item.quantity, 0);
  cartSummary.textContent = `${itemCount} item(s), total $${cart.total}.`;
}

async function checkHealth() {
  try {
    const health = await request("/health");
    healthDot.className = "dot ok";
    healthText.textContent = `${health.service} is ${health.status}`;
    writeLog("GET /health", health);
  } catch (error) {
    healthDot.className = "dot bad";
    healthText.textContent = "API unavailable";
    writeLog("GET /health failed", error.payload || error.message);
  }
}

async function loadProducts() {
  try {
    const payload = await request("/api/products");
    products = payload.products;
    renderProducts();
    writeLog("GET /api/products", payload);
  } catch (error) {
    writeLog("GET /api/products failed", error.payload || error.message);
  }
}

async function loadCart() {
  const sessionId = sessionInput.value.trim();
  if (!sessionId) {
    cartSummary.textContent = "Add a product first or paste a session id.";
    return;
  }

  try {
    const cart = await request(`/api/cart/${sessionId}`);
    renderCart(cart);
    writeLog(`GET /api/cart/${sessionId}`, cart);
  } catch (error) {
    writeLog("GET /api/cart failed", error.payload || error.message);
  }
}

document.querySelector("#load-products").addEventListener("click", loadProducts);
document.querySelector("#load-cart").addEventListener("click", loadCart);
document.querySelector("#clear-log").addEventListener("click", () => {
  responseLog.textContent = "{}";
});

document.querySelector("#cart-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const body = {
    product_id: Number(productSelect.value),
    quantity: Number(document.querySelector("#quantity").value),
  };
  const existingSession = sessionInput.value.trim();
  if (existingSession) {
    body.session_id = existingSession;
  }

  try {
    const payload = await request("/api/cart", {
      method: "POST",
      body: JSON.stringify(body),
    });
    sessionInput.value = payload.session_id;
    await loadCart();
    writeLog("POST /api/cart", payload);
  } catch (error) {
    writeLog("POST /api/cart failed", error.payload || error.message);
  }
});

document.querySelector("#place-order").addEventListener("click", async () => {
  const sessionId = sessionInput.value.trim();
  if (!sessionId) {
    cartSummary.textContent = "Add a product before placing an order.";
    return;
  }

  try {
    const order = await request("/api/orders", {
      method: "POST",
      body: JSON.stringify({ session_id: sessionId }),
    });
    cartSummary.textContent = `Order ${order.order_id} confirmed for $${order.total}.`;
    sessionInput.value = "";
    writeLog("POST /api/orders", order);
  } catch (error) {
    writeLog("POST /api/orders failed", error.payload || error.message);
  }
});

checkHealth();
loadProducts();
