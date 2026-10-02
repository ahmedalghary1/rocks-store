(() => {
  const shell = document.querySelector('[data-product-video-shell]');
  const video = shell?.querySelector('[data-product-video]');
  const toggle = shell?.querySelector('[data-product-video-toggle]');
  const label = toggle?.querySelector('[data-product-video-label]');
  if (!shell || !video || !toggle || !label) return;

  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  let inView = false;
  let userPaused = reducedMotion.matches;

  const syncButton = () => {
    const playing = !video.paused && !video.ended;
    const text = playing ? toggle.dataset.pauseLabel : toggle.dataset.playLabel;
    toggle.setAttribute('aria-pressed', String(playing));
    toggle.setAttribute('aria-label', text);
    label.textContent = text;
  };

  const playVideo = async () => {
    try {
      await video.play();
    } catch {
      video.controls = true;
      toggle.hidden = true;
    }
  };

  video.controls = false;
  toggle.hidden = false;
  video.addEventListener('play', syncButton);
  video.addEventListener('pause', syncButton);

  toggle.addEventListener('click', () => {
    if (video.paused) {
      userPaused = false;
      playVideo();
    } else {
      userPaused = true;
      video.pause();
    }
  });

  if ('IntersectionObserver' in window) {
    const observer = new IntersectionObserver(entries => {
      const entry = entries[0];
      inView = entry.isIntersecting && entry.intersectionRatio >= .55;
      if (inView && !reducedMotion.matches && !userPaused) playVideo();
      if (!inView && !video.paused) video.pause();
    }, {threshold: [0, .55, 1]});
    observer.observe(shell);
  }

  reducedMotion.addEventListener?.('change', event => {
    if (event.matches) {
      userPaused = true;
      video.pause();
    }
  });

  document.addEventListener('visibilitychange', () => {
    if (document.hidden) video.pause();
    else if (inView && !reducedMotion.matches && !userPaused) playVideo();
  });
  syncButton();
})();
