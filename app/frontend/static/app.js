const API_BASE = "";

const state = {
  token: localStorage.getItem("access_token") || "",
  user: null,
};

function qs(id) {
  return document.getElementById(id);
}

function showToast(message) {
  const toast = qs("toast");
  toast.textContent = message;
  toast.classList.remove("hidden");
  setTimeout(() => toast.classList.add("hidden"), 3200);
}

function formatJson(data) {
  return JSON.stringify(data, null, 2);
}

function authHeaders(extra = {}) {
  const headers = { ...extra };
  if (state.token) headers.Authorization = `Bearer ${state.token}`;
  return headers;
}

async function apiRequest(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, options);
  const contentType = response.headers.get("content-type") || "";
  let data;
  if (contentType.includes("application/json")) {
    data = await response.json();
  } else {
    data = await response.text();
  }

  if (!response.ok) {
    const error = {
      status: response.status,
      statusText: response.statusText,
      detail: data,
    };
    throw error;
  }
  return data;
}

function renderOutput(elementId, data) {
  qs(elementId).textContent = typeof data === "string" ? data : formatJson(data);
}

function renderError(elementId, error) {
  renderOutput(elementId, {
    error: true,
    status: error.status || "Network error",
    detail: error.detail || error.message || error,
  });
}

function updateLoginStatus() {
  const status = qs("loginStatus");
  const logoutBtn = qs("logoutBtn");
  if (state.user) {
    status.textContent = `Đang đăng nhập: ${state.user.username} (${state.user.role})`;
    logoutBtn.classList.remove("hidden");
  } else if (state.token) {
    status.textContent = "Đã có token, bấm GET /users/me để kiểm tra";
    logoutBtn.classList.remove("hidden");
  } else {
    status.textContent = "Chưa đăng nhập";
    logoutBtn.classList.add("hidden");
  }
}

// PKCE Helpers
function generateRandomString(length) {
    const array = new Uint32Array(length);
    window.crypto.getRandomValues(array);
    return Array.from(array, dec => ('0' + dec.toString(16)).substr(-2)).join('');
}

async function generateCodeChallenge(codeVerifier) {
    const encoder = new TextEncoder();
    const data = encoder.encode(codeVerifier);
    const digest = await window.crypto.subtle.digest('SHA-256', data);
    return btoa(String.fromCharCode.apply(null, new Uint8Array(digest)))
        .replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

async function loginWithKeycloak() {
    const codeVerifier = generateRandomString(32);
    localStorage.setItem('pkce_code_verifier', codeVerifier);
    const codeChallenge = await generateCodeChallenge(codeVerifier);
    
    // Redirect URI là trang hiện tại
    const redirectUri = window.location.origin + window.location.pathname;
    
    const loginUrl = new URL('http://localhost:8081/realms/capstone/protocol/openid-connect/auth');
    loginUrl.searchParams.append('client_id', 'frontend-app');
    loginUrl.searchParams.append('response_type', 'code');
    loginUrl.searchParams.append('scope', 'openid profile');
    loginUrl.searchParams.append('redirect_uri', redirectUri);
    loginUrl.searchParams.append('code_challenge', codeChallenge);
    loginUrl.searchParams.append('code_challenge_method', 'S256');
    
    window.location.href = loginUrl.toString();
}

async function handleKeycloakCallback() {
    const urlParams = new URLSearchParams(window.location.search);
    const code = urlParams.get('code');
    if (!code) return false;

    const codeVerifier = localStorage.getItem('pkce_code_verifier');
    const redirectUri = window.location.origin + window.location.pathname;

    const body = new URLSearchParams({
        grant_type: 'authorization_code',
        client_id: 'frontend-app',
        code: code,
        redirect_uri: redirectUri,
        code_verifier: codeVerifier
    });
    
    try {
        const response = await fetch('http://localhost:8081/realms/capstone/protocol/openid-connect/token', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: body
        });
        const data = await response.json();
        if (data.access_token) {
            state.token = data.access_token;
            localStorage.setItem('access_token', data.access_token);
            // remove code from URL
            window.history.replaceState({}, document.title, window.location.pathname);
            showToast("Đăng nhập thành công qua Keycloak");
            return true;
        }
    } catch(e) {
        console.error("Lỗi khi đổi token:", e);
    }
    return false;
}

async function loadMe() {
  try {
    const data = await apiRequest("/users/me", {
      headers: authHeaders(),
    });
    state.user = data;
    updateLoginStatus();
    renderOutput("meOutput", data);
    return data;
  } catch (error) {
    state.user = null;
    updateLoginStatus();
    renderError("meOutput", error);
    throw error;
  }
}

function renderOrders(orders) {
  const list = qs("ordersList");
  if (!orders.length) {
    list.innerHTML = "<p class='hint'>Chưa có đơn hàng.</p>";
    return;
  }

  list.innerHTML = orders.map(order => `
    <div class="order-card">
      <strong>Order #${order.id}: ${escapeHtml(order.item_name)}</strong>
      <span>Số tiền: ${Number(order.amount).toLocaleString("vi-VN")} VND</span>
      <span>Trạng thái: ${escapeHtml(order.status)}</span>
      <span>owner_id: ${order.owner_id}</span>
    </div>
  `).join("");
}

function escapeHtml(text) {
  return String(text)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

async function loadOrders(outputTarget = null) {
  const data = await apiRequest("/orders/", {
    headers: authHeaders(),
  });
  renderOrders(data);
  if (outputTarget) renderOutput(outputTarget, data);
  return data;
}

function setupEvents() {
  const kcBtn = qs("kcLoginBtn");
  if (kcBtn) {
    kcBtn.addEventListener("click", async () => {
      await loginWithKeycloak();
    });
  }

  qs("logoutBtn").addEventListener("click", () => {
    state.token = "";
    state.user = null;
    localStorage.removeItem("access_token");
    updateLoginStatus();
    renderOutput("meOutput", "Đã đăng xuất.");
    qs("ordersList").innerHTML = "";
    showToast("Đã đăng xuất");
  });

  qs("meBtn").addEventListener("click", async () => {
    try {
      await loadMe();
    } catch (_) {}
  });

  qs("loadOrdersBtn").addEventListener("click", async () => {
    try {
      await loadOrders();
      showToast("Đã tải đơn hàng");
    } catch (error) {
      qs("ordersList").innerHTML = `<pre class="output">${escapeHtml(formatJson(error))}</pre>`;
    }
  });

  qs("createOrderForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
      const payload = {
        item_name: qs("itemName").value.trim(),
        amount: Number(qs("amount").value),
        status: qs("status").value,
      };
      const data = await apiRequest("/orders/", {
        method: "POST",
        headers: authHeaders({ "Content-Type": "application/json" }),
        body: JSON.stringify(payload),
      });
      renderOutput("createOrderOutput", data);
      await loadOrders();
      showToast("Tạo đơn hàng thành công");
    } catch (error) {
      renderError("createOrderOutput", error);
    }
  });

  qs("testVulnerableBtn").addEventListener("click", async () => {
    const orderId = qs("bolaOrderId").value;
    try {
      const data = await apiRequest(`/orders/vulnerable/${orderId}`, {
        headers: authHeaders(),
      });
      renderOutput("vulnerableOutput", data);
    } catch (error) {
      renderError("vulnerableOutput", error);
    }
  });

  qs("testSecureBtn").addEventListener("click", async () => {
    const orderId = qs("bolaOrderId").value;
    try {
      const data = await apiRequest(`/orders/${orderId}`, {
        headers: authHeaders(),
      });
      renderOutput("secureOutput", data);
    } catch (error) {
      renderError("secureOutput", error);
    }
  });

  qs("loadUsersBtn").addEventListener("click", async () => {
    try {
      const data = await apiRequest("/users/", {
        headers: authHeaders(),
      });
      renderOutput("adminOutput", data);
    } catch (error) {
      renderError("adminOutput", error);
    }
  });

  qs("adminLoadOrdersBtn").addEventListener("click", async () => {
    try {
      const data = await loadOrders("adminOutput");
      renderOutput("adminOutput", data);
    } catch (error) {
      renderError("adminOutput", error);
    }
  });
  qs("testSsrfVulnerableBtn").addEventListener("click", async () => {
    const url = qs("ssrfUrl").value;
    try {
      const data = await apiRequest(`/fetch/vulnerable?url=${encodeURIComponent(url)}`, {
        headers: authHeaders(),
      });
      renderOutput("ssrfVulnerableOutput", data);
    } catch (error) {
      renderError("ssrfVulnerableOutput", error);
    }
  });

  qs("testSsrfSecureBtn").addEventListener("click", async () => {
    const url = qs("ssrfUrl").value;
    try {
      const data = await apiRequest(`/fetch/secure?url=${encodeURIComponent(url)}`, {
        headers: authHeaders(),
      });
      renderOutput("ssrfSecureOutput", data);
    } catch (error) {
      renderError("ssrfSecureOutput", error);
    }
  });

  qs("testWebhookVulnerableBtn").addEventListener("click", async () => {
    const payload = qs("webhookData").value;
    try {
      const data = await apiRequest("/webhooks/vulnerable", {
        method: "POST",
        headers: authHeaders({ "Content-Type": "application/json" }),
        body: payload,
      });
      renderOutput("webhookVulnerableOutput", data);
    } catch (error) {
      renderError("webhookVulnerableOutput", error);
    }
  });

  qs("testWebhookSecureBtn").addEventListener("click", async () => {
    const payload = qs("webhookData").value;
    const signature = qs("webhookSignature").value;
    try {
      const data = await apiRequest("/webhooks/secure", {
        method: "POST",
        headers: authHeaders({
          "Content-Type": "application/json",
          "X-Hub-Signature-256": signature,
        }),
        body: payload,
      });
      renderOutput("webhookSecureOutput", data);
    } catch (error) {
      renderError("webhookSecureOutput", error);
    }
  });

  qs("testExposureVulnerableBtn").addEventListener("click", async () => {
    try {
      const data = await apiRequest("/users/exposure/vulnerable", {
        headers: authHeaders(),
      });
      renderOutput("exposureVulnerableOutput", data);
    } catch (error) {
      renderError("exposureVulnerableOutput", error);
    }
  });

  qs("testExposureSecureBtn").addEventListener("click", async () => {
    try {
      const data = await apiRequest("/users/exposure/secure", {
        headers: authHeaders(),
      });
      renderOutput("exposureSecureOutput", data);
    } catch (error) {
      renderError("exposureSecureOutput", error);
    }
  });
}

window.addEventListener("DOMContentLoaded", async () => {
  setupEvents();
  
  // Kiểm tra nếu là callback từ Keycloak
  const isCallback = await handleKeycloakCallback();
  
  updateLoginStatus();
  if (state.token) {
    try {
      await loadMe();
    } catch (_) {
      localStorage.removeItem("access_token");
      state.token = "";
      updateLoginStatus();
    }
  }
});
