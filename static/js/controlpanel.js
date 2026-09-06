'use strict';

document.addEventListener('DOMContentLoaded', () => {
  window.lucide?.createIcons({attrs: {'stroke-width': 1.8, 'aria-hidden': 'true'}});
  const body = document.body;
  const sidebar = document.getElementById('cpSidebar');
  const openButton = document.querySelector('[data-sidebar-open]');
  const closeButtons = document.querySelectorAll('[data-sidebar-close]');
  const setSidebar = open => {
    body.classList.toggle('cp-sidebar-open', open);
    openButton?.setAttribute('aria-expanded', String(open));
    sidebar?.setAttribute('aria-hidden', String(!open && matchMedia('(max-width: 860px)').matches));
  };
  openButton?.addEventListener('click', () => setSidebar(true));
  closeButtons.forEach(button => button.addEventListener('click', () => setSidebar(false)));
  document.addEventListener('keydown', event => { if (event.key === 'Escape') setSidebar(false); });
  matchMedia('(max-width: 860px)').addEventListener('change', () => setSidebar(false));

  const selectAll = document.querySelector('[data-select-all]');
  selectAll?.addEventListener('change', () => {
    document.querySelectorAll('input[name="selected"]').forEach(input => { input.checked = selectAll.checked; });
  });
});
