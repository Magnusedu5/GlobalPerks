// Backend URL — update this one line when you add a custom domain to the backend on Render.
window.GP_BACKEND = (location.hostname === 'localhost' || location.hostname === '127.0.0.1')
  ? 'http://localhost:8000'
  : 'https://globalperks.onrender.com';
