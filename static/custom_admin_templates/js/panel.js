// ElectroShop Panel — panel.js

// ── Sidebar toggle (mobile) ───────────────────────────
const sidebar  = document.getElementById('sidebar');
const overlay  = document.getElementById('sidebarOverlay');
const menuBtn  = document.getElementById('menuToggle');
const closeBtn = document.getElementById('sidebarClose');

function openSidebar() {
  sidebar.classList.add('open');
  overlay.classList.add('open');
  document.body.style.overflow = 'hidden';
}

function closeSidebar() {
  sidebar.classList.remove('open');
  overlay.classList.remove('open');
  document.body.style.overflow = '';
}

menuBtn  && menuBtn.addEventListener('click', openSidebar);
closeBtn && closeBtn.addEventListener('click', closeSidebar);
overlay  && overlay.addEventListener('click', closeSidebar);

// ── Auto-dismiss flash messages ───────────────────────
document.querySelectorAll('.flash').forEach(el => {
  setTimeout(() => el.style.opacity = '0', 4000);
  setTimeout(() => el.remove(), 4400);
  el.style.transition = 'opacity .4s';
});
