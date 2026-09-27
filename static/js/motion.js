(() => {
  'use strict';

  const gsap = window.gsap;
  const ScrollTrigger = window.ScrollTrigger;
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const finePointer = window.matchMedia('(hover: hover) and (pointer: fine)').matches;
  const rtl = document.documentElement.dir === 'rtl';
  const all = (selector, scope = document) => gsap ? gsap.utils.toArray(selector, scope) : [...scope.querySelectorAll(selector)];

  // The storefront remains fully visible and usable if GSAP is unavailable.
  document.querySelectorAll('.reveal').forEach(element => element.classList.add('visible'));
  if (!gsap || !ScrollTrigger || reduceMotion) {
    document.documentElement.classList.add('motion-ready');
    return;
  }

  gsap.registerPlugin(ScrollTrigger);
  document.documentElement.classList.add('motion-ready');
  const ease = 'power3.out';
  const side = rtl ? -1 : 1;
  const mm = gsap.matchMedia();

  const reveal = (targets, options = {}) => {
    const elements = all(targets);
    if (!elements.length) return;
    const trigger = options.trigger || elements[0];
    gsap.from(elements, {
      autoAlpha: 0,
      y: options.y ?? 34,
      x: options.x ?? 0,
      scale: options.scale ?? 1,
      duration: options.duration ?? .82,
      stagger: options.stagger ?? .08,
      ease: options.ease || ease,
      clearProps: 'opacity,visibility,transform',
      scrollTrigger: {
        trigger,
        start: options.start || 'top 84%',
        once: true,
      },
    });
  };

  const loadTimeline = gsap.timeline({ defaults: { ease, clearProps: 'opacity,visibility,transform' } });
  loadTimeline
    .from('.topbar', { autoAlpha: 0, y: -18, duration: .38 })
    .from('.site-header', { autoAlpha: 0, y: -24, duration: .55 }, '-=.24');

  const hero = document.querySelector('.ev-hero');
  if (hero) {
    const heroTimeline = gsap.timeline({ defaults: { ease, clearProps: 'opacity,visibility,transform' }, delay: .08 });
    heroTimeline
      .from('.ev-hero__media img', { scale: 1.07, duration: 1.35, ease: 'power2.out' })
      .from('.ev-hero__shade', { autoAlpha: 0, duration: .7 }, '<')
      .from('.ev-hero__copy .ev-kicker', { autoAlpha: 0, y: 18, duration: .55 }, '-=.85')
      .from('.ev-hero__copy h1', { autoAlpha: 0, y: 44, duration: .9 }, '-=.38')
      .from('.ev-hero__copy>p', { autoAlpha: 0, y: 22, duration: .65 }, '-=.52')
      .from('.ev-hero__copy .ev-button', { autoAlpha: 0, y: 18, scale: .97, duration: .55 }, '-=.38')
      .from('.ev-feature-row article', { autoAlpha: 0, y: 22, duration: .58, stagger: .09 }, '-=.28');

    mm.add('(min-width: 701px)', () => {
      gsap.to('.ev-hero__media img', {
        yPercent: 7,
        ease: 'none',
        scrollTrigger: { trigger: hero, start: 'top top', end: 'bottom top', scrub: .8 },
      });
      gsap.to('.ev-hero__copy', {
        y: 42,
        autoAlpha: .72,
        ease: 'none',
        scrollTrigger: { trigger: hero, start: 'top top', end: '70% top', scrub: .7 },
      });
    });
  } else {
    const pageHero = document.querySelector('.page-hero');
    if (pageHero) {
      const parts = all('.breadcrumb, .eyebrow, h1, p', pageHero);
      gsap.from(parts, { autoAlpha: 0, y: 25, duration: .72, stagger: .08, delay: .16, ease, clearProps: 'opacity,visibility,transform' });
    }
  }

  // Homepage: alternating intensity keeps the page from feeling like a demo reel.
  reveal('.ev-section-title > *', { trigger: '.ev-section-title', y: 28, stagger: .09 });
  reveal('.ev-product-card', { trigger: '.ev-product-grid', y: 38, scale: .985, stagger: .11 });
  reveal('.ev-proof__grid article', { trigger: '.ev-proof', y: 18, stagger: .08, duration: .68 });
  reveal('.ev-proof__statement', { trigger: '.ev-proof', x: 34 * side, y: 0, duration: .82 });
  reveal('.ev-about__copy > *', { trigger: '.ev-about', x: -34 * side, y: 0, stagger: .07 });
  reveal('.ev-about__visual', { trigger: '.ev-about', y: 0, scale: .965, duration: 1 });
  reveal('.ev-about__aside > *', { trigger: '.ev-about', x: 28 * side, y: 0, stagger: .07 });
  mm.add('(min-width: 901px)', () => {
    const image = document.querySelector('.ev-about__visual img');
    if (image) gsap.fromTo(image, { yPercent: -5, scale: 1.06 }, { yPercent: 5, ease: 'none', scrollTrigger: { trigger: '.ev-about', start: 'top bottom', end: 'bottom top', scrub: .8 } });
  });

  // Shared commerce and content sections.
  all('.section-head').forEach(section => reveal(all(':scope > *', section), { trigger: section, y: 26, stagger: .08 }));
  all('.product-grid').forEach(grid => reveal(all(':scope > .product-card', grid), { trigger: grid, y: 30, scale: .985, stagger: .075 }));
  reveal('.catalog-toolbar', { y: 18 });
  reveal('.filters', { x: -24 * side, y: 0, duration: .72 });
  reveal('.about-grid > div', { x: 30 * side, y: 0, stagger: .13 });
  reveal('.values-grid > article', { y: 32, stagger: .12 });
  reveal('.contact-info > *', { x: -28 * side, y: 0, stagger: .075 });
  reveal('.contact-form > *', { trigger: '.contact-form', x: 24 * side, y: 0, stagger: .055 });
  reveal('.gallery', { x: -30 * side, y: 0, duration: .9 });
  reveal('.product-summary > *', { trigger: '.product-summary', x: 26 * side, y: 0, stagger: .055 });
  reveal('.detail-tabs', { y: 28 });
  reveal('.spec-grid > div', { trigger: '.spec-grid', y: 20, stagger: .06 });
  reveal('.cart-item', { trigger: '.cart-lines', x: -24 * side, y: 0, stagger: .07 });
  reveal('.checkout-fields > section', { trigger: '.checkout-fields', y: 28, stagger: .1 });
  reveal('.order-summary', { x: 26 * side, y: 0, duration: .78 });
  reveal('.account-grid > *', { y: 28, stagger: .1 });
  reveal('.order-card', { y: 20, stagger: .07 });
  reveal('.success-page .success-mark, .success-page .eyebrow, .success-page h1, .success-page>div>p, .order-number, .success-grid>div', { trigger: '.success-page', y: 26, stagger: .08 });
  reveal('.auth-card > *', { trigger: '.auth-card', y: 22, stagger: .07, start: 'top 90%' });
  reveal('.legal-copy > *', { trigger: '.legal-copy', y: 20, stagger: .055 });
  reveal('.empty-state > *', { trigger: '.empty-state', y: 18, stagger: .07 });

  const footer = document.querySelector('.rocks-footer');
  if (footer) {
    reveal('.rocks-footer__grid > *', { trigger: footer, y: 30, stagger: .09, start: 'top 92%' });
    reveal('.rocks-footer__bottom > *', { trigger: '.rocks-footer__bottom', y: 16, stagger: .08, start: 'top 96%' });
  }

  // Pointer lighting follows the cursor without tilting product photography.
  if (finePointer) {
    all('.product-card, .ev-product-card, .values-grid>article').forEach(card => {
      card.addEventListener('pointermove', event => {
        const bounds = card.getBoundingClientRect();
        card.style.setProperty('--motion-x', `${event.clientX - bounds.left}px`);
        card.style.setProperty('--motion-y', `${event.clientY - bounds.top}px`);
      }, { passive: true });
    });
  }

  // Animate UI panels when existing application code opens them.
  const animateOpenPanel = (element, target, from) => {
    if (!element || !target) return;
    new MutationObserver(() => {
      if (!element.classList.contains('open')) return;
      gsap.fromTo(target, from, { autoAlpha: 1, x: 0, y: 0, scale: 1, duration: .42, ease, clearProps: 'opacity,visibility,transform' });
    }).observe(element, { attributes: true, attributeFilter: ['class'] });
  };
  animateOpenPanel(document.querySelector('.mobile-drawer'), document.querySelector('.mobile-drawer'), { autoAlpha: 0, x: 35 * side });
  animateOpenPanel(document.querySelector('#searchOverlay'), document.querySelector('#searchOverlay .search-shell'), { autoAlpha: 0, y: -22, scale: .985 });
  animateOpenPanel(document.querySelector('#quickModal'), document.querySelector('#quickModal .quick-dialog'), { autoAlpha: 0, y: 24, scale: .975 });

  addEventListener('load', () => ScrollTrigger.refresh(), { once: true });
})();
