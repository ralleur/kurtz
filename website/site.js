'use strict';
const comparison = document.querySelector('[data-player-comparison]');
if (comparison) {
  const switcher = comparison.querySelector('.state-switch');
  const image = comparison.querySelector('img');
  const caption = comparison.querySelector('figcaption');
  switcher.hidden = false;
  switcher.addEventListener('click', event => {
    const button = event.target.closest('button[data-state]');
    if (!button) return;
    const controls = button.dataset.state === 'controls';
    image.src = `assets/desktop-${controls ? 'controls' : 'clean'}-1152.webp`;
    image.alt = `The same Caminandes frame in kurtz on a staged desktop, with playback controls ${controls ? 'visible' : 'hidden'}.`;
    caption.textContent = controls ? 'Real kurtz capture. Controls visible. Same frame, same staged desktop.' : 'Real kurtz capture. Controls hidden. Same frame, same staged desktop.';
    switcher.querySelectorAll('button').forEach(item => item.setAttribute('aria-pressed', String(item === button)));
  });
}
