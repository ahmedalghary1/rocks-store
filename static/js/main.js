const $ = (selector, scope = document) => scope.querySelector(selector);
const $$ = (selector, scope = document) => [...scope.querySelectorAll(selector)];
const csrf = () => document.cookie.split('; ').find(row => row.startsWith('csrftoken='))?.split('=')[1] || '';
const escapeHtml = value => String(value).replace(/[&<>'"]/g, char => ({ '&':'&amp;', '<':'&lt;', '>':'&gt;', "'":'&#39;', '"':'&quot;' })[char]);
const renderIcons = (root = document) => window.lucide?.createIcons({ root, attrs: { 'stroke-width': 1.8, 'aria-hidden': 'true' } });
const iconMarkup = (name) => `<i data-lucide="${name}" aria-hidden="true"></i>`;
const upgradeLegacyIcons = () => {
  $$('.product-art span').forEach(el => { const name = el.textContent.trim(); if (!el.querySelector('[data-lucide]') && /^[a-z-]+$/.test(name)) el.innerHTML = iconMarkup(name); });
  $$('.zoom-btn').forEach(el => { el.innerHTML = iconMarkup('zoom-in'); });
  $$('.filter-toggle').forEach(el => { el.innerHTML = `${iconMarkup('sliders-horizontal')}<span>الفلاتر</span>`; });
  $$('.filter-close,.modal-close').forEach(el => { el.innerHTML = iconMarkup('x'); });
  $$('.remove-item').forEach(el => { el.innerHTML = iconMarkup('trash-2'); });
  $$('.secondary-actions [data-wishlist]').forEach(el => { el.innerHTML = `${iconMarkup('heart')}<span>أضف للمفضلة</span>`; });
  const trustIcons = ['shield-check', 'refresh-cw', 'badge-check'];
  $$('.purchase-trust span').forEach((el, index) => { el.textContent = el.textContent.replace(/^[◇↺▣]\s*/, ''); el.insertAdjacentHTML('afterbegin', iconMarkup(trustIcons[index] || 'check')); });
  $$('.empty-state>span').forEach(el => { el.innerHTML = iconMarkup(el.closest('.wishlist-page') ? 'heart' : 'package'); });
};
upgradeLegacyIcons(); renderIcons();

const header = $('#siteHeader');
const updateHeader = () => header?.classList.toggle('scrolled', scrollY > 24);
addEventListener('scroll', updateHeader, { passive: true }); updateHeader();

const drawer = $('.mobile-drawer');
const toggleDrawer = open => {
  drawer?.classList.toggle('open', open); drawer?.setAttribute('aria-hidden', String(!open));
  $('.menu-toggle')?.setAttribute('aria-expanded', String(open)); document.body.style.overflow = open ? 'hidden' : '';
};
$('.menu-toggle')?.addEventListener('click', () => toggleDrawer(true));
$('.drawer-close')?.addEventListener('click', () => toggleDrawer(false));

const searchOverlay = $('#searchOverlay');
const toggleSearch = open => {
  searchOverlay?.classList.toggle('open', open); searchOverlay?.setAttribute('aria-hidden', String(!open));
  document.body.style.overflow = open ? 'hidden' : '';
  if (open) setTimeout(() => $('#liveSearch')?.focus(), 100);
};
$$('[data-search-open]').forEach(button => button.addEventListener('click', () => toggleSearch(true)));
$$('[data-search-close]').forEach(button => button.addEventListener('click', () => toggleSearch(false)));

let searchTimer;
$('#liveSearch')?.addEventListener('input', event => {
  clearTimeout(searchTimer); const input = event.currentTarget; const target = $('#searchResults');
  searchTimer = setTimeout(async () => {
    if (input.value.trim().length < 2) { target.innerHTML = '<p>اكتب حرفين على الأقل لبدء البحث.</p>'; return; }
    target.innerHTML = '<p>نبحث في مجموعة ROCKS…</p>';
    try {
      const response = await fetch(`${input.dataset.url}?q=${encodeURIComponent(input.value)}`);
      const data = await response.json();
      target.innerHTML = data.results.length ? data.results.map(item => `<a class="search-result" href="${escapeHtml(item.url)}"><span><b>${escapeHtml(item.name)}</b><small>${escapeHtml(item.category)}</small></span><strong>${Number(item.price).toLocaleString('ar-EG')} ج.م</strong></a>`).join('') : '<div class="empty-search"><b>لا توجد نتائج مطابقة</b><p>جرّب اسمًا أقصر أو ابحث بكود المنتج.</p></div>';
    } catch { target.innerHTML = '<p>تعذّر البحث الآن. حاول مرة أخرى.</p>'; }
  }, 280);
});

const toast = message => {
  const el = document.createElement('div'); el.className = 'toast'; el.textContent = message;
  $('#toastStack').append(el); setTimeout(() => el.remove(), 3200);
};
setTimeout(() => $$('.toast').forEach(el => el.remove()), 3800);

$$('.ajax-cart').forEach(form => form.addEventListener('submit', async event => {
  event.preventDefault(); const button = $('button[type=submit]', form); button.disabled = true;
  try {
    const response = await fetch(form.action, { method: 'POST', body: new FormData(form), headers: { 'X-Requested-With': 'XMLHttpRequest', 'X-CSRFToken': csrf() } });
    const data = await response.json();
    if (!response.ok) throw new Error(data.message || 'تعذرت الإضافة.');
    $$('[data-cart-count]').forEach(el => el.textContent = data.count); toast(data.message);
    button.animate([{ transform: 'scale(.9)' }, { transform: 'scale(1.08)' }, { transform: 'scale(1)' }], { duration: 380 });
  } catch (error) { toast(error.message || 'تعذرت الإضافة. حاول مرة أخرى.'); } finally { button.disabled = false; }
}));

const formatMoney = value => `${Number(value).toFixed(2)} ج.م`;
let cartUpdatePending = Promise.resolve();
const updateCartForm = form => {
  const runUpdate = async () => {
    const input = $('[data-cart-qty-input]', form);
    const buttons = $$('button', form);
    buttons.forEach(button => { button.disabled = true; });
    try {
      const response = await fetch(form.action, {
        method: 'POST', body: new FormData(form),
        headers: { 'X-Requested-With': 'XMLHttpRequest', 'X-CSRFToken': csrf() },
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.message || 'تعذر تحديث الكمية.');
      input.value = data.quantity;
      const line = form.closest('.cart-item');
      const lineTotal = $('[data-cart-line-total]', line);
      if (lineTotal) lineTotal.textContent = formatMoney(data.item_total);
      $$('[data-cart-count]').forEach(el => { el.textContent = data.count; });
      const itemsCount = $('[data-cart-items-count]');
      if (itemsCount) itemsCount.textContent = data.count;
      const subtotal = $('[data-cart-subtotal]');
      const shipping = $('[data-cart-shipping]');
      const discount = $('[data-cart-discount]');
      const discountRow = $('[data-cart-discount-row]');
      const total = $('[data-cart-total]');
      const couponSaving = $('[data-coupon-saving]');
      if (subtotal) subtotal.textContent = formatMoney(data.subtotal);
      if (shipping) shipping.textContent = Number(data.shipping) ? formatMoney(data.shipping) : 'مجاني';
      if (discount) discount.textContent = `-${formatMoney(data.discount)}`;
      if (discountRow) discountRow.hidden = !Number(data.discount);
      if (couponSaving) couponSaving.textContent = formatMoney(data.discount);
      if (total) total.textContent = formatMoney(data.total);
    } catch (error) {
      toast(error.message || 'تعذر تحديث الكمية.');
    } finally {
      buttons.forEach(button => { button.disabled = false; });
    }
  };
  cartUpdatePending = cartUpdatePending.catch(() => {}).then(runUpdate);
  return cartUpdatePending;
};
$$('[data-cart-update]').forEach(form => {
  const input = $('[data-cart-qty-input]', form);
  form.addEventListener('submit', event => { event.preventDefault(); updateCartForm(form); });
  $('[data-cart-qty-minus]', form)?.addEventListener('click', () => {
    input.value = Math.max(Number(input.min || 1), Number(input.value || 1) - 1);
    updateCartForm(form);
  });
  $('[data-cart-qty-plus]', form)?.addEventListener('click', () => {
    input.value = Math.min(Number(input.max || Infinity), Number(input.value || 1) + 1);
    updateCartForm(form);
  });
  input?.addEventListener('change', () => {
    input.value = Math.min(Number(input.max || Infinity), Math.max(Number(input.min || 1), Number(input.value || 1)));
    updateCartForm(form);
  });
});
$('.cart-checkout-link')?.addEventListener('click', async event => {
  event.preventDefault();
  const target = event.currentTarget.href;
  await cartUpdatePending.catch(() => {});
  window.location.assign(target);
});

$$('[data-wishlist]').forEach(button => button.addEventListener('click', async () => {
  try {
    const response = await fetch(button.dataset.url, { method: 'POST', headers: { 'X-CSRFToken': csrf(), 'X-Requested-With': 'XMLHttpRequest' } });
    const data = await response.json(); button.classList.toggle('active', data.active); button.setAttribute('aria-pressed', String(data.active));
    toast(data.active ? 'تمت إضافة المنتج إلى المفضلة' : 'تمت إزالة المنتج من المفضلة');
  } catch { toast('تعذر تحديث المفضلة.'); }
}));

const modal = $('#quickModal');
$$('[data-quick]').forEach(button => button.addEventListener('click', async () => {
  const content = $('#quickContent'); content.innerHTML = '<p>يتم تحميل التفاصيل…</p>'; modal.classList.add('open'); modal.setAttribute('aria-hidden', 'false');
  const response = await fetch(button.dataset.quick); content.innerHTML = await response.text(); renderIcons(content);
  const form = $('.ajax-cart', content); if (form) form.addEventListener('submit', async event => { event.preventDefault(); const response = await fetch(form.action, { method:'POST', body:new FormData(form), headers:{'X-Requested-With':'XMLHttpRequest','X-CSRFToken':csrf()} }); const data=await response.json(); $$('[data-cart-count]').forEach(el=>el.textContent=data.count); toast(data.message); });
}));
$('.modal-close')?.addEventListener('click', () => { modal.classList.remove('open'); modal.setAttribute('aria-hidden', 'true'); });

$('.filter-toggle')?.addEventListener('click', () => $('.filters')?.classList.add('open'));
$('.filter-close')?.addEventListener('click', () => $('.filters')?.classList.remove('open'));
$$('[data-qty-minus]').forEach(button => button.addEventListener('click', () => { const input = button.nextElementSibling; input.value = Math.max(Number(input.min), Number(input.value) - 1); }));
$$('[data-qty-plus]').forEach(button => button.addEventListener('click', () => { const input = button.previousElementSibling; input.value = Math.min(Number(input.max), Number(input.value) + 1); }));
$$('[data-tab]').forEach(button => button.addEventListener('click', () => { $$('.tab-buttons button,.tab-panel').forEach(el => el.classList.remove('active')); button.classList.add('active'); $(`#${button.dataset.tab}`).classList.add('active'); }));
const variantSelect = $('[data-variant-select]');
variantSelect?.addEventListener('change', event => {
  const option = event.currentTarget.selectedOptions[0];
  const form = $('#detail-cart-form'); const quantity = $('input[name=quantity]', form); const submit = $('button[type=submit]', form);
  const selected = Boolean(option?.value); const stock = Number(option?.dataset.stock || 0);
  if (quantity && selected) { quantity.max = stock; quantity.value = Math.min(Number(quantity.value), stock); }
  if ($('[data-product-price]') && selected) $('[data-product-price]').textContent = Number(option.dataset.price).toLocaleString('ar-EG', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  if ($('[data-product-sku]') && selected) $('[data-product-sku]').textContent = option.dataset.sku;
  if ($('[data-mobile-price]') && selected) $('[data-mobile-price]').textContent = Number(option.dataset.price).toLocaleString('ar-EG', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  if ($('[data-mobile-variant]')) $('[data-mobile-variant]').value = option?.value || '';
  if (submit) submit.disabled = !selected || stock < 1;
  const mobileSubmit = $('.mobile-add button[type=submit]'); if (mobileSubmit) mobileSubmit.disabled = !selected || stock < 1;
});
$$('[data-gallery-image]').forEach(button => button.addEventListener('click', () => {
  const image = $('[data-main-image] img'); if (!image) return;
  image.src = button.dataset.galleryImage; image.alt = button.dataset.galleryAlt || image.alt;
}));
$('.zoom-btn')?.addEventListener('click', event => {
  const target = $('[data-main-image]'); const zoomed = target?.classList.toggle('zoomed');
  event.currentTarget.setAttribute('aria-pressed', String(Boolean(zoomed)));
});
$$('[data-submit-once]').forEach(button => button.closest('form').addEventListener('submit', () => { button.disabled = true; button.textContent = 'جارٍ تأكيد الطلب…'; }));

const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;
const motionDirections = ['right', 'left', 'bottom', 'top'];
const motionTargets = [
  ...$$('.topbar, .site-header'),
  ...$$('main > section'),
  ...$$('.newsletter, .footer'),
];
const detailTargets = $$([
  '.reveal', '.category-card', '.cart-item', '.checkout-fields > section',
  '.order-summary', '.spec-grid > div', '.values-grid > article',
  '.why-cards > article', '.order-card', '.success-grid > div',
].join(','));
const uniqueMotionTargets = [...new Set([...motionTargets, ...detailTargets])];
uniqueMotionTargets.forEach((element, index) => {
  element.classList.add('motion-item', `motion-from-${motionDirections[index % motionDirections.length]}`);
  element.style.setProperty('--motion-delay', `${Math.min((index % 6) * 65, 325)}ms`);
});

const revealMotion = () => {
  document.documentElement.classList.add('page-ready');
  if (reducedMotion || !('IntersectionObserver' in window)) {
    uniqueMotionTargets.forEach(element => element.classList.add('visible'));
    return;
  }
  const observer = new IntersectionObserver(entries => entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.classList.add('visible');
      observer.unobserve(entry.target);
    }
  }), { threshold: .08, rootMargin: '0px 0px -4% 0px' });
  uniqueMotionTargets.forEach(element => observer.observe(element));
};
window.setTimeout(() => requestAnimationFrame(revealMotion), reducedMotion ? 0 : 90);
addEventListener('keydown', event => { if (event.key === 'Escape') { toggleSearch(false); toggleDrawer(false); modal?.classList.remove('open'); } });
