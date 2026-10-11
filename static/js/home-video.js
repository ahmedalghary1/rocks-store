(() => {
  const shells = [...document.querySelectorAll('[data-product-video-shell]')];
  if (!shells.length) return;

  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  const saveData = Boolean(navigator.connection?.saveData);
  const players = shells.map(shell => {
    const video = shell.querySelector('[data-product-video]');
    const toggle = shell.querySelector('[data-product-video-toggle]');
    const label = toggle?.querySelector('[data-product-video-label]');
    if (!video || !toggle || !label) return null;

    let userPaused = reducedMotion.matches || saveData;
    let inView = false;
    let sourceLoaded = false;
    const syncButton = () => {
      const playing = !video.paused && !video.ended;
      const text = playing ? toggle.dataset.pauseLabel : toggle.dataset.playLabel;
      toggle.setAttribute('aria-pressed', String(playing));
      toggle.setAttribute('aria-label', text);
      label.textContent = text;
    };
    const playVideo = async () => {
      if (!sourceLoaded) {
        video.querySelectorAll('source[data-src]').forEach(source => {
          source.src = source.dataset.src;
          source.removeAttribute('data-src');
        });
        video.load();
        sourceLoaded = true;
      }
      try {
        await video.play();
      } catch {
        video.controls = true;
        toggle.hidden = true;
      }
    };

    video.autoplay = false;
    video.loop = true;
    video.muted = true;
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

    reducedMotion.addEventListener?.('change', event => {
      if (event.matches) {
        userPaused = true;
        video.pause();
      }
    });
    document.addEventListener('visibilitychange', () => {
      if (document.hidden) video.pause();
      else if (inView && !userPaused && !reducedMotion.matches) playVideo();
    });
    syncButton();
    return {shell, video, playVideo, get inView() { return inView; }, set inView(value) { inView = value; }, get userPaused() { return userPaused; }};
  });

  if ('IntersectionObserver' in window) {
    const observer = new IntersectionObserver(entries => {
      entries.forEach(entry => {
        const player = players.find(item => item?.shell === entry.target);
        if (!player) return;
        player.inView = entry.isIntersecting && entry.intersectionRatio >= .12;
        if (!player.inView) player.video.pause();
        else if (!document.hidden && !reducedMotion.matches && !player.userPaused) player.playVideo();
      });
    }, {threshold: [0, .12, .35]});
    players.forEach(player => { if (player) observer.observe(player.shell); });
  }
})();
