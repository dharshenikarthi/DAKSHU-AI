/**
 * DAKSHU AI - Common Application & Authentication Utilities
 */

const API_BASE = window.location.protocol === 'file:' ? 'http://127.0.0.1:8000/api' : '/api';

const DakshuApp = {
  // Token & User Persistence
  getToken() {
    return localStorage.getItem('dakshu_token') || null;
  },

  getUser() {
    try {
      const u = localStorage.getItem('dakshu_user');
      return u ? JSON.parse(u) : null;
    } catch (e) {
      return null;
    }
  },

  setAuth(token, user) {
    if (token) localStorage.setItem('dakshu_token', token);
    if (user) localStorage.setItem('dakshu_user', JSON.stringify(user));
  },

  clearAuth() {
    localStorage.removeItem('dakshu_token');
    localStorage.removeItem('dakshu_user');
  },

  isAuthenticated() {
    return !!this.getToken();
  },

  // Convenience API Get/Post helpers
  async apiGet(endpoint) {
    try {
      const res = await this.fetchWithAuth(endpoint, { method: 'GET' });
      return res.ok ? await res.json() : null;
    } catch (e) {
      console.warn('apiGet failed for', endpoint, e);
      return null;
    }
  },

  async apiPost(endpoint, data = {}) {
    try {
      const res = await this.fetchWithAuth(endpoint, {
        method: 'POST',
        body: JSON.stringify(data)
      });
      return res.ok ? await res.json() : null;
    } catch (e) {
      console.warn('apiPost failed for', endpoint, e);
      return null;
    }
  },

  // API Client wrapper
  async fetchWithAuth(endpoint, options = {}) {
    const headers = options.headers || {};
    const token = this.getToken();

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    if (!headers['Content-Type'] && !(options.body instanceof FormData)) {
      headers['Content-Type'] = 'application/json';
    }

    const response = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers
    });

    if (response.status === 401) {
      // Session expired or unauthenticated
      this.clearAuth();
      const path = window.location.pathname;
      if (!path.includes('login') && !path.includes('register') && !path.endsWith('index.html') && !path.endsWith('chat.html') && path !== '/') {
        window.location.href = 'login.html';
      }
    }

    return response;
  },

  // Toast Notification
  showToast(message, type = 'info') {
    let toastContainer = document.getElementById('dakshu-toast-container');
    if (!toastContainer) {
      toastContainer = document.createElement('div');
      toastContainer.id = 'dakshu-toast-container';
      toastContainer.style.position = 'fixed';
      toastContainer.style.bottom = '24px';
      toastContainer.style.right = '24px';
      toastContainer.style.zIndex = '9999';
      toastContainer.style.display = 'flex';
      toastContainer.style.flexDirection = 'column';
      toastContainer.style.gap = '8px';
      document.body.appendChild(toastContainer);
    }

    const toast = document.createElement('div');
    toast.className = 'glass-card';
    toast.style.padding = '12px 20px';
    toast.style.borderRadius = '12px';
    toast.style.fontSize = '0.9rem';
    toast.style.fontWeight = '500';
    toast.style.maxWidth = '360px';
    toast.style.boxShadow = '0 8px 24px rgba(0,0,0,0.5)';
    toast.style.animation = 'fadeIn 0.25s ease-out';

    if (type === 'error') {
      toast.style.borderLeft = '4px solid #f43f5e';
      toast.style.background = 'rgba(24, 12, 24, 0.9)';
      toast.style.color = '#fda4af';
    } else if (type === 'success') {
      toast.style.borderLeft = '4px solid #10b981';
      toast.style.background = 'rgba(12, 28, 22, 0.9)';
      toast.style.color = '#6ee7b7';
    } else {
      toast.style.borderLeft = '4px solid #06b6d4';
      toast.style.background = 'rgba(12, 22, 38, 0.9)';
      toast.style.color = '#67e8f9';
    }

    toast.innerText = message;
    toastContainer.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(8px)';
      toast.style.transition = 'all 0.3s ease';
      setTimeout(() => toast.remove(), 300);
    }, 3500);
  },

  // Navbar Dynamic Authentication Sync
  updateNavState() {
    const navActions = document.getElementById('nav-actions');
    if (!navActions) return;

    const user = this.getUser();
    if (user && this.isAuthenticated()) {
      navActions.innerHTML = `
        <a href="chat.html" class="btn btn-cyan" style="padding: 0.55rem 1.2rem; font-size: 0.88rem;">
          <i data-lucide="message-square" style="width: 16px; height: 16px;"></i> Chat with Dakshu
        </a>
        <a href="profile.html" class="btn btn-secondary" style="padding: 0.55rem 1.2rem; font-size: 0.88rem;" title="Profile & Personal Memories">
          <i data-lucide="user" style="width: 16px; height: 16px;"></i> ${user.full_name ? user.full_name.split(' ')[0] : 'Profile'}
        </a>
        <button id="nav-logout-btn" class="btn btn-icon" title="Logout" style="width: 36px; height: 36px;">
          <i data-lucide="log-out" style="width: 16px; height: 16px;"></i>
        </button>
      `;

      const logoutBtn = document.getElementById('nav-logout-btn');
      if (logoutBtn) {
        logoutBtn.addEventListener('click', async () => {
          try {
            await fetch(`${API_BASE}/auth/logout`, { method: 'POST' });
          } catch (e) {}
          DakshuApp.clearAuth();
          window.location.href = 'index.html';
        });
      }
    } else {
      navActions.innerHTML = `
        <a href="login.html" class="btn btn-secondary" style="padding: 0.55rem 1.2rem; font-size: 0.88rem;">Log In</a>
        <a href="register.html" class="btn btn-primary" style="padding: 0.55rem 1.2rem; font-size: 0.88rem;">Get Started</a>
      `;
    }

    if (window.lucide) {
      window.lucide.createIcons();
    }
  }
};

// Auto-run on DOMContentLoaded
document.addEventListener('DOMContentLoaded', () => {
  DakshuApp.updateNavState();
  if (window.lucide) {
    window.lucide.createIcons();
  }
});

window.DakshuApp = DakshuApp;

