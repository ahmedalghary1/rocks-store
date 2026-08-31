const $ = (selector, scope = document) => scope.querySelector(selector);
const $$ = (selector, scope = document) => [...scope.querySelectorAll(selector)];
const csrf = () => document.cookie.split('; ').find(row => row.startsWith('csrftoken='))?.split('=')[1] || '';
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
      target.innerHTML = data.results.length ? data.results.map(item => `<a class="search-result" href="${item.url}"><span><b>${item.name}</b><small>${item.category}</small></span><strong>${Number(item.price).toLocaleString('ar-EG')} ج.م</strong></a>`).join('') : '<div class="empty-search"><b>لا توجد نتائج مطابقة</b><p>جرّب اسمًا أقصر أو ابحث بكود المنتج.</p></div>';
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
    if (!response.ok) throw new Error();
    $$('[data-cart-count]').forEach(el => el.textContent = data.count); toast(data.message);
    button.animate([{ transform: 'scale(.9)' }, { transform: 'scale(1.08)' }, { transform: 'scale(1)' }], { duration: 380 });
  } catch { toast('تعذرت الإضافة. حاول مرة أخرى.'); } finally { button.disabled = false; }
}));

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
$$('[data-submit-once]').forEach(button => button.closest('form').addEventListener('submit', () => { button.disabled = true; button.textContent = 'جارٍ تأكيد الطلب…'; }));

const observer = new IntersectionObserver(entries => entries.forEach(entry => { if (entry.isIntersecting) { entry.target.classList.add('visible'); observer.unobserve(entry.target); } }), { threshold: .08 });
$$('.reveal').forEach(el => observer.observe(el));
addEventListener('keydown', event => { if (event.key === 'Escape') { toggleSearch(false); toggleDrawer(false); modal?.classList.remove('open'); } });
