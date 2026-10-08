/**
 * Kitchen Dashboard Live Interactivity & Polling
 */

document.addEventListener('DOMContentLoaded', () => {
  const kitchenContainer = document.getElementById('kitchenOrdersContainer');
  if (!kitchenContainer) return;

  let soundEnabled = true;
  let pollInterval = null;
  let lastKnownOrderCount = parseInt(kitchenContainer.dataset.initialCount || '0');

  // Audio tone synthesizer for new incoming orders
  function playOrderNotification() {
    if (!soundEnabled) return;
    try {
      const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
      const osc = audioCtx.createOscillator();
      const gainNode = audioCtx.createGain();

      osc.type = 'sine';
      osc.frequency.setValueAtTime(587.33, audioCtx.currentTime); // D5
      osc.frequency.exponentialRampToValueAtTime(880, audioCtx.currentTime + 0.15); // A5

      gainNode.gain.setValueAtTime(0.2, audioCtx.currentTime);
      gainNode.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.35);

      osc.connect(gainNode);
      gainNode.connect(audioCtx.destination);

      osc.start();
      osc.stop(audioCtx.currentTime + 0.35);
    } catch (e) {
      console.warn('AudioContext not allowed or not supported yet:', e);
    }
  }

  // Sound toggle button
  const soundToggleBtn = document.getElementById('soundToggleBtn');
  if (soundToggleBtn) {
    soundToggleBtn.addEventListener('click', () => {
      soundEnabled = !soundEnabled;
      soundToggleBtn.classList.toggle('btn-outline-light', !soundEnabled);
      soundToggleBtn.classList.toggle('btn-success', soundEnabled);
      soundToggleBtn.innerHTML = soundEnabled 
        ? '<i class="bi bi-volume-up-fill me-1"></i> Sound ON'
        : '<i class="bi bi-volume-mute-fill me-1"></i> Sound OFF';
    });
  }

  // Handle status update buttons (advance or select)
  document.addEventListener('click', async (e) => {
    const actionBtn = e.target.closest('.btn-kitchen-action');
    if (!actionBtn) return;

    const orderId = actionBtn.dataset.orderId;
    const action = actionBtn.dataset.action; // 'advance'
    const newStatus = actionBtn.dataset.status;

    actionBtn.disabled = true;
    const originalText = actionBtn.innerHTML;
    actionBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Updating...';

    try {
      const response = await fetch(`/kitchen/order/${orderId}/status/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCookie('csrftoken'),
          'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({ action: action, status: newStatus })
      });

      const data = await response.json();
      if (response.ok && data.success) {
        // Reload ticket or page state
        window.location.reload();
      } else {
        alert(data.error || 'Failed to update order status');
        actionBtn.disabled = false;
        actionBtn.innerHTML = originalText;
      }
    } catch (err) {
      console.error('Status update failed:', err);
      window.location.reload();
    }
  });

  // Auto-poll for new orders every 10 seconds
  function startPolling() {
    pollInterval = setInterval(async () => {
      try {
        const response = await fetch('/api/kitchen/orders/', {
          headers: { 'X-Requested-With': 'XMLHttpRequest' }
        });
        if (!response.ok) return;

        const data = await response.json();
        if (data.count > lastKnownOrderCount) {
          playOrderNotification();
          // Reload dashboard to show new incoming ticket
          window.location.reload();
        }
        lastKnownOrderCount = data.count;
      } catch (err) {
        // Silently tolerate temporary network blips
      }
    }, 10000);
  }

  startPolling();
});
