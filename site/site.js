document.querySelectorAll('[data-copy-target]').forEach((button) => {
  button.addEventListener('click', async () => {
    const target = document.getElementById(button.dataset.copyTarget);
    if (!target) return;
    const message = target.textContent.trim();
    const original = button.textContent;
    try {
      await navigator.clipboard.writeText(message);
      button.textContent = 'Copied first task ✓';
      window.setTimeout(() => { button.textContent = original; }, 2200);
    } catch {
      button.textContent = 'Select the text above to copy';
      window.setTimeout(() => { button.textContent = original; }, 3000);
    }
  });
});
