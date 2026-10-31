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

  document.querySelectorAll('[data-product-picker]').forEach(picker => {
    picker.querySelector('[data-product-search]')?.addEventListener('input', event => {
      const query = event.target.value.trim().toLocaleLowerCase();
      picker.querySelectorAll('.cp-product-picker-list input[type="checkbox"]').forEach(input => {
        const row = input.closest('label')?.parentElement;
        if (row) row.hidden = !row.textContent.toLocaleLowerCase().includes(query);
      });
    });
  });

  const galleryEditor = document.querySelector('[data-gallery-editor]');
  const galleryUpload = galleryEditor?.querySelector('[data-gallery-upload]');
  const mainImageUpload = galleryEditor?.querySelector('#id_main_image');
  const deleteMainImage = galleryEditor?.querySelector('[data-delete-main-image]');
  deleteMainImage?.addEventListener('change', () => {
    const currentRadio = galleryEditor.querySelector('input[name="gallery_primary"][value="current"]');
    if (deleteMainImage.checked) {
      if (currentRadio) currentRadio.checked = false;
    } else if (currentRadio && !galleryEditor.querySelector('input[name="gallery_primary"]:checked')) {
      currentRadio.checked = true;
    }
  });
  galleryEditor?.querySelectorAll('[data-delete-gallery-image]').forEach(checkbox => {
    checkbox.addEventListener('change', () => {
      if (!checkbox.checked) return;
      const tile = checkbox.closest('.cp-gallery-tile');
      const radio = tile?.querySelector('input[name="gallery_primary"]');
      if (radio) radio.checked = false;
      const currentRadio = galleryEditor.querySelector('input[name="gallery_primary"][value="current"]');
      if (!deleteMainImage?.checked && currentRadio && !galleryEditor.querySelector('input[name="gallery_primary"]:checked')) {
        currentRadio.checked = true;
      }
    });
  });
  mainImageUpload?.addEventListener('change', () => {
    if (mainImageUpload.files.length) {
      if (deleteMainImage) deleteMainImage.checked = false;
      galleryEditor.querySelectorAll('input[name="gallery_primary"]').forEach(radio => { radio.checked = false; });
    }
  });
  galleryUpload?.addEventListener('change', () => {
    const previews = galleryEditor.querySelector('[data-gallery-previews]');
    previews.replaceChildren();
    Array.from(galleryUpload.files).forEach((file, index) => {
      const label = document.createElement('label');
      label.className = 'cp-gallery-tile';
      const picture = document.createElement('img');
      picture.alt = file.name;
      picture.src = URL.createObjectURL(file);
      picture.addEventListener('load', () => URL.revokeObjectURL(picture.src), {once: true});
      const caption = document.createElement('span');
      const radio = document.createElement('input');
      radio.type = 'radio';
      radio.name = 'gallery_primary';
      radio.value = `new:${index}`;
      caption.append(radio, document.createTextNode(' تعيين كرئيسية'));
      label.append(picture, caption);
      previews.append(label);
    });
    if (!deleteMainImage?.checked && !galleryEditor.querySelector('input[name="gallery_primary"]:checked')) {
      galleryEditor.querySelector('input[name="gallery_primary"]')?.click();
    }
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

  document.querySelectorAll('.cp-editor').forEach(form => {
    form.addEventListener('submit', event => {
      const submitter = event.submitter;
      if (submitter?.name) {
        const intent = document.createElement('input');
        intent.type = 'hidden';
        intent.name = submitter.name;
        intent.value = submitter.value;
        form.append(intent);
      }
      form.querySelectorAll('button[type="submit"]').forEach(button => {
        button.dataset.originalMarkup ||= button.innerHTML;
        button.disabled = true;
        button.setAttribute('aria-busy', 'true');
      });
      if (submitter) submitter.textContent = 'جاري حفظ المنتج والصورة…';
    });
  });

  addEventListener('pageshow', () => {
    document.querySelectorAll('.cp-editor button[type="submit"]').forEach(button => {
      button.disabled = false;
      button.removeAttribute('aria-busy');
      if (button.dataset.originalMarkup) button.innerHTML = button.dataset.originalMarkup;
    });
  });
});
