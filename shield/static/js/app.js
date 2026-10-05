(() => {
  const navButton = document.querySelector('[data-nav-toggle]');
  const nav = document.querySelector('#site-nav');
  if (navButton && nav) {
    navButton.addEventListener('click', () => {
      const open = nav.classList.toggle('is-open');
      navButton.setAttribute('aria-expanded', String(open));
    });
  }

  document.querySelectorAll('[data-dismiss]').forEach((button) => {
    button.addEventListener('click', () => button.closest('.flash')?.remove());
  });

  const exit = document.querySelector('[data-quick-exit]');
  if (exit) {
    exit.addEventListener('click', (event) => {
      event.preventDefault();
      window.location.replace(exit.href);
    });
  }

  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && event.shiftKey && exit) {
      window.location.replace(exit.href);
    }
  });

  // Disable the submit control after a valid submit so a slow page load
  // can't be double-submitted. This never calls preventDefault(), so the
  // browser's own submission (and any server-side re-render on invalid
  // input) proceeds exactly as before.
  document.querySelectorAll('form').forEach((form) => {
    form.addEventListener('submit', () => {
      const control = form.querySelector('[type="submit"]');
      if (!control || control.disabled) return;
      setTimeout(() => {
        control.disabled = true;
        control.classList.add('is-submitting');
        const prop = control.tagName === 'INPUT' ? 'value' : 'textContent';
        control.dataset.originalLabel = control[prop];
        control[prop] = 'Submitting…';
      }, 0);
    });
  });
})();
