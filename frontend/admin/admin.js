// ============================================================
// GlobalPerks Admin Panel — Shared Auth & API Utilities
// ============================================================
// Pages:
//   /admin/login.html                     Login
//   /admin/bookings.html                  Bookings list
//   /admin/booking.html?id=<id>           Booking detail
//   /admin/galleries.html                 Galleries list
//   /admin/gallery.html?slug=<slug>       Gallery detail + photo upload
//   /admin/cms.html                       Site content editor
//
// Backend admin API root: /api/admin/
//   POST   /api/admin/login/
//   POST   /api/admin/logout/
//   GET    /api/admin/bookings/?status=
//   GET    /api/admin/bookings/<id>/
//   PATCH  /api/admin/bookings/<id>/
//   GET    /api/admin/galleries/
//   POST   /api/admin/galleries/
//   GET    /api/admin/galleries/<slug>/
//   PATCH  /api/admin/galleries/<slug>/
//   DELETE /api/admin/galleries/<slug>/
//   POST   /api/admin/galleries/<slug>/photos/
//   DELETE /api/admin/galleries/<slug>/photos/<id>/
//   GET    /api/admin/cms/
//   POST   /api/admin/cms/text/
//   POST   /api/admin/cms/image/
//   DELETE /api/admin/cms/image/<key>/
// ============================================================

const GP = {
  TOKEN_KEY: 'gp_admin_token',
  B: window.GP_BACKEND,

  getToken() {
    return localStorage.getItem(this.TOKEN_KEY);
  },

  setToken(t) {
    localStorage.setItem(this.TOKEN_KEY, t);
  },

  clearToken() {
    localStorage.removeItem(this.TOKEN_KEY);
  },

  _decodePayload(token) {
    try {
      const part = token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/');
      // atob requires base64 to be padded to a multiple of 4
      const padded = part + '='.repeat((4 - part.length % 4) % 4);
      return JSON.parse(atob(padded));
    } catch (e) { return null; }
  },

  // Call at top of every protected page. Returns token or redirects to login.
  requireAuth() {
    const token = this.getToken();
    if (!token) { window.location.href = '/admin/login'; return null; }
    const payload = this._decodePayload(token);
    if (!payload || (payload.exp && Date.now() / 1000 > payload.exp)) {
      this.clearToken();
      window.location.href = '/admin/login';
      return null;
    }
    return token;
  },

  // Authenticated fetch. Automatically attaches Bearer token.
  // Returns null and redirects on 401; otherwise returns the Response.
  async fetch(path, options = {}) {
    const token = this.requireAuth();
    if (!token) return null;

    const headers = { 'Authorization': 'Bearer ' + token };
    // Let browser set Content-Type for FormData (needs boundary)
    if (options.body && !(options.body instanceof FormData)) {
      headers['Content-Type'] = 'application/json';
    }

    const res = await fetch(this.B + path, {
      ...options,
      headers: { ...headers, ...(options.headers || {}) },
    });

    if (res.status === 401) {
      this.clearToken();
      window.location.href = '/admin/login';
      return null;
    }
    return res;
  },

  async logout() {
    try { await this.fetch('/api/admin/logout/', { method: 'POST' }); } catch (e) {}
    this.clearToken();
    window.location.href = '/admin/login';
  },

  // Call once on page load: checks auth + wires logout button.
  init() {
    this.requireAuth();
    const btn = document.getElementById('logout-btn');
    if (btn) btn.addEventListener('click', () => this.logout());
    // Highlight active nav link
    document.querySelectorAll('.nav-link').forEach(a => {
      if (a.href && window.location.pathname.startsWith(new URL(a.href).pathname.replace('.html', ''))) {
        a.classList.add('active');
      }
    });
  },
};
