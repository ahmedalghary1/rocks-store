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

  const lengthFormset = document.querySelector('[data-length-formset]');
  if (lengthFormset) {
    const rows = lengthFormset.querySelector('[data-formset-rows]');
    const template = lengthFormset.querySelector('[data-empty-length-form]');
    const total = lengthFormset.querySelector('[name$="-TOTAL_FORMS"]');

    lengthFormset.addEventListener('click', event => {
      const removeButton = event.target.closest('[data-remove-length]');
      if (removeButton) {
        const row = removeButton.closest('[data-formset-row]');
        const deleteInput = row?.querySelector('input[name$="-DELETE"]');
        if (deleteInput) deleteInput.checked = true;
        if (row) row.hidden = true;
        return;
      }

      if (!event.target.closest('[data-add-length]') || !template || !total || !rows) return;
      const index = Number(total.value);
      rows.insertAdjacentHTML('beforeend', template.innerHTML.replaceAll('__prefix__', index));
      total.value = index + 1;
      const newRow = rows.lastElementChild;
      window.lucide?.createIcons({root: newRow});
      newRow?.querySelector('input:not([type="hidden"])')?.focus();
    });
  }
});
