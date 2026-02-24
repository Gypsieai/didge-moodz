document.addEventListener('DOMContentLoaded', () => {
  const statusEl = document.getElementById('status');
  const logEl = document.getElementById('log');

  const log = (msg) => {
    const time = new Date().toLocaleTimeString();
    logEl.textContent += `[${time}] ${msg}\n`;
    logEl.scrollTop = logEl.scrollHeight;
  };

  const setStatus = (msg) => {
    statusEl.textContent = `Status: ${msg}`;
  };

  document.getElementById('runBtn').addEventListener('click', () => {
    setStatus('Running diagnostic...');
    log('Diagnostic started');
    // Placeholder for real diagnostic logic
    setTimeout(() => {
      log('Diagnostic completed successfully');
      setStatus('Idle');
    }, 1500);
  });

  document.getElementById('resetBtn').addEventListener('click', () => {
    setStatus('Resetting system...');
    log('System reset initiated');
    setTimeout(() => {
      log('System reset complete');
      setStatus('Idle');
    }, 800);
  });

  document.getElementById('showBtn').addEventListener('click', () => {
    setStatus('Showing results');
    log('Results displayed (placeholder)');
    setTimeout(() => setStatus('Idle'), 500);
  });
});
