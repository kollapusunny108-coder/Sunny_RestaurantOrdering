/**
 * Main Site JS: Search, Filter Enhancements & Order Tracking Realtime Poller
 */

document.addEventListener('DOMContentLoaded', () => {
  // Live tracker poller if tracker container is present
  const trackerEl = document.getElementById('orderTrackerContainer');
  if (trackerEl) {
    const orderId = trackerEl.dataset.orderId;
    let currentStatus = trackerEl.dataset.currentStatus;

    if (orderId && currentStatus !== 'COMPLETED' && currentStatus !== 'CANCELLED') {
      const pollTimer = setInterval(async () => {
        try {
          const res = await fetch(`/api/order/${orderId}/status/`);
          if (!res.ok) return;

          const data = await res.json();
          if (data.status !== currentStatus) {
            currentStatus = data.status;
            // Update UI elements
            const badgeEl = document.getElementById('orderStatusBadge');
            if (badgeEl) {
              badgeEl.textContent = data.status_display;
              badgeEl.className = `badge fs-6 ${data.badge_class}`;
            }

            // Update Progress Steps
            const progressLine = document.getElementById('trackerProgressLine');
            const step = data.status_step;

            if (progressLine) {
              const widths = { 1: '0%', 2: '33%', 3: '66%', 4: '100%' };
              progressLine.style.width = widths[step] || '0%';
            }

            // Update step nodes
            for (let i = 1; i <= 4; i++) {
              const nodeEl = document.getElementById(`stepNode${i}`);
              if (!nodeEl) continue;

              nodeEl.classList.remove('active', 'completed');
              if (i < step) {
                nodeEl.classList.add('completed');
              } else if (i === step) {
                nodeEl.classList.add('active');
              }
            }

            // If completed, play gentle sound or stop polling
            if (data.status === 'COMPLETED' || data.status === 'CANCELLED') {
              clearInterval(pollTimer);
              const toastEl = document.createElement('div');
              toastEl.className = 'alert alert-success mt-3';
              toastEl.innerHTML = '<i class="bi bi-check-circle-fill me-2"></i> Your order has been completed! Enjoy your meal!';
              trackerEl.prepend(toastEl);
            }
          }
        } catch (e) {
          console.warn('Tracker poll error:', e);
        }
      }, 5000);
    }
  }

  // Client-side quick filter for food cards if on menu page
  const searchInput = document.getElementById('menuSearchInput');
  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      const term = e.target.value.toLowerCase().trim();
      const cards = document.querySelectorAll('.food-card-col');
      cards.forEach(card => {
        const title = card.querySelector('.food-title')?.textContent.toLowerCase() || '';
        const desc = card.querySelector('.food-description')?.textContent.toLowerCase() || '';
        if (title.includes(term) || desc.includes(term)) {
          card.style.display = '';
        } else {
          card.style.display = 'none';
        }
      });
    });
  }
});
