(() => {
  const shells = [...document.querySelectorAll('[data-product-video-shell]')];
  if (!shells.length) return;

  const section = document.querySelector('[data-product-video-section]');
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  let sectionInView = false;
  let hasStarted = false;
  const players = shells.map(shell => {
    const video = shell.querySelector('[data-product-video]');
    const toggle = shell.querySelector('[data-product-video-toggle]');
    const label = toggle?.querySelector('[data-product-video-label]');
    if (!video || !toggle || !label) return null;

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

    video.autoplay = true;
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
      else if (hasStarted && !userPaused && !reducedMotion.matches) playVideo();
    });
    syncButton();
    return {video, playVideo, get userPaused() { return userPaused; }, set userPaused(value) { userPaused = value; }};
  });

  if ('IntersectionObserver' in window && section) {
    const observer = new IntersectionObserver(entries => {
      const entry = entries[0];
      sectionInView = entry.isIntersecting && entry.intersectionRatio >= .12;
      if (sectionInView && !reducedMotion.matches) {
        hasStarted = true;
        players.forEach(player => {
          if (player && !player.userPaused) player.playVideo();
        });
      }
    }, {threshold: [0, .12, .35]});
    observer.observe(section);
  }
})();
