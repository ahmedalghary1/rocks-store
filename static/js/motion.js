(() => {
  'use strict';

  // Motion is progressive enhancement and must never delay first paint.
  document.documentElement.classList.add('motion-ready');
  document.querySelectorAll('.reveal').forEach(element => element.classList.add('visible'));

  // Preserve the small pointer-lighting detail without an animation engine.
  if (!window.matchMedia('(hover: hover) and (pointer: fine)').matches) return;

  document.querySelectorAll('.product-card, .ev-product-card, .values-grid>article').forEach(card => {
    card.addEventListener('pointermove', event => {
      const bounds = card.getBoundingClientRect();
      card.style.setProperty('--motion-x', `${event.clientX - bounds.left}px`);
      card.style.setProperty('--motion-y', `${event.clientY - bounds.top}px`);
    }, { passive: true });
  });
})();
