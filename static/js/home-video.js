(() => {
  const shells = [...document.querySelectorAll('[data-product-video-shell]')];
  if (!shells.length) return;

  const section = document.querySelector('[data-product-video-section]');
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  const players = shells.map((shell, index) => {
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
      if (video.ended) video.currentTime = 0;
      try {
        await video.play();
      } catch {
        video.controls = true;
        toggle.hidden = true;
      }
    };

    const player = {
      video,
      playVideo,
      get userPaused() { return userPaused; },
      set userPaused(value) { userPaused = value; },
    };
    video.controls = false;
    toggle.hidden = false;
    video.addEventListener('play', () => {
      players.forEach(other => {
        if (other && other.video !== video && !other.video.paused) {
          other.userPaused = true;
          other.video.pause();
        }
      });
      syncButton();
    });
    video.addEventListener('pause', syncButton);
    video.addEventListener('ended', () => {
      if (index === 0 && players[1]) {
        players[1].userPaused = false;
        players[1].playVideo();
      }
    });
    video.addEventListener('pointerenter', event => {
      if (event.pointerType === 'mouse') {
        userPaused = false;
        playVideo();
      }
    });
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
    });
    syncButton();
    return player;
  });

  if ('IntersectionObserver' in window && section) {
    const observer = new IntersectionObserver(entries => {
      const entry = entries[0];
      const inView = entry.isIntersecting && entry.intersectionRatio >= .12;
      if (inView && !reducedMotion.matches && !players[0]?.userPaused) players[0]?.playVideo();
      if (!inView) {
        players.forEach(player => player?.video.pause());
        if (players[0]) players[0].userPaused = false;
      }
    }, {threshold: [0, .12, .35]});
    observer.observe(section);
  }
})();
