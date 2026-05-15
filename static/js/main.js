/* ============================================================
   Task Manager – Shared JavaScript
   ============================================================ */

// Display today's date in the topbar
(function () {
  const el = document.getElementById('dateDisplay');
  if (el) {
    el.textContent = new Date().toLocaleDateString('en-US', {
      weekday: 'short', year: 'numeric', month: 'short', day: 'numeric'
    });
  }
})();
