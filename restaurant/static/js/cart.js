/**
 * Smart Restaurant Shopping Cart Engine
 * Synchronizes browser localStorage with Django Session Cart API
 */

// Helper to get CSRF cookie in Django
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

const csrftoken = getCookie('csrftoken');

class RestaurantCart {
  constructor() {
    this.storageKey = 'restaurant_cart_state';
    this.initEventListeners();
    this.refreshCartUI();
  }

  initEventListeners() {
    // Add to cart buttons
    document.addEventListener('click', (e) => {
      const addBtn = e.target.closest('.btn-add-cart');
      if (addBtn) {
        const itemId = addBtn.dataset.itemId;
        this.addItem(itemId, 1, addBtn);
      }

      // Quantity buttons inside offcanvas drawer or checkout page
      const qtyBtn = e.target.closest('.qty-btn');
      if (qtyBtn) {
        const itemId = qtyBtn.dataset.itemId;
        const action = qtyBtn.dataset.action; // 'inc' or 'dec'
        this.changeQuantity(itemId, action);
      }

      // Remove item buttons
      const removeBtn = e.target.closest('.btn-remove-item');
      if (removeBtn) {
        const itemId = removeBtn.dataset.itemId;
        this.removeItem(itemId);
      }

      // Clear cart button
      const clearBtn = e.target.closest('.btn-clear-cart');
      if (clearBtn) {
        this.clearCart();
      }
    });
  }

  async addItem(itemId, quantity = 1, triggerBtn = null) {
    if (triggerBtn) {
      triggerBtn.disabled = true;
      triggerBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Adding...';
    }

    try {
      const response = await fetch('/api/cart/add/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrftoken,
          'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({ item_id: itemId, quantity: quantity })
      });

      const data = await response.json();

      if (response.ok && data.success) {
        this.updateBadgeCounts(data.cart_count);
        this.saveLocalCartCount(data.cart_count);
        this.showToast('success', data.message || 'Added to order!');
        await this.refreshCartUI();

        // Open offcanvas drawer automatically on first add or trigger pulse
        const cartDrawerEl = document.getElementById('cartOffcanvas');
        if (cartDrawerEl && typeof bootstrap !== 'undefined') {
          const bsDrawer = bootstrap.Offcanvas.getOrCreateInstance(cartDrawerEl);
          bsDrawer.show();
        }
      } else {
        this.showToast('danger', data.error || 'Could not add item to cart');
      }
    } catch (err) {
      console.error('Cart add error:', err);
      this.showToast('danger', 'Network error. Please try again.');
    } finally {
      if (triggerBtn) {
        triggerBtn.disabled = false;
        triggerBtn.innerHTML = '<i class="bi bi-plus-lg me-1"></i> Add to Order';
      }
    }
  }

  async changeQuantity(itemId, action) {
    try {
      // Find current quantity from UI element or compute
      const qtyEl = document.querySelector(`.qty-val[data-item-id="${itemId}"]`);
      let currentQty = qtyEl ? parseInt(qtyEl.textContent) : 1;
      let newQty = action === 'inc' ? currentQty + 1 : currentQty - 1;

      const response = await fetch('/api/cart/update/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrftoken,
          'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({ item_id: itemId, quantity: newQty })
      });

      const data = await response.json();
      if (response.ok && data.success) {
        this.updateBadgeCounts(data.cart_count);
        this.saveLocalCartCount(data.cart_count);
        await this.refreshCartUI();
      } else {
        this.showToast('danger', data.error || 'Failed to update quantity');
      }
    } catch (err) {
      console.error('Cart update error:', err);
    }
  }

  async removeItem(itemId) {
    try {
      const response = await fetch('/api/cart/remove/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrftoken,
          'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({ item_id: itemId })
      });

      const data = await response.json();
      if (response.ok && data.success) {
        this.updateBadgeCounts(data.cart_count);
        this.saveLocalCartCount(data.cart_count);
        this.showToast('info', 'Item removed from cart');
        await this.refreshCartUI();
      }
    } catch (err) {
      console.error('Cart remove error:', err);
    }
  }

  async clearCart() {
    try {
      const response = await fetch('/api/cart/clear/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrftoken,
          'X-Requested-With': 'XMLHttpRequest'
        }
      });

      const data = await response.json();
      if (response.ok && data.success) {
        this.updateBadgeCounts(0);
        localStorage.removeItem(this.storageKey);
        await this.refreshCartUI();
        this.showToast('info', 'Cart cleared');
      }
    } catch (err) {
      console.error('Cart clear error:', err);
    }
  }

  async refreshCartUI() {
    try {
      const response = await fetch('/api/cart/data/', {
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
      });
      if (!response.ok) return;

      const data = await response.json();
      this.updateBadgeCounts(data.cart_count);
      this.saveLocalCartCount(data.cart_count);

      // Render Offcanvas Drawer Items
      const drawerContainer = document.getElementById('cartDrawerItems');
      const drawerEmpty = document.getElementById('cartDrawerEmpty');
      const drawerFooter = document.getElementById('cartDrawerFooter');

      const drawerSubtotal = document.getElementById('drawerSubtotal');
      const drawerTax = document.getElementById('drawerTax');
      const drawerTotal = document.getElementById('drawerTotal');

      if (drawerSubtotal) drawerSubtotal.textContent = `$${data.subtotal}`;
      if (drawerTax) drawerTax.textContent = `$${data.tax}`;
      if (drawerTotal) drawerTotal.textContent = `$${data.grand_total}`;

      if (drawerContainer && drawerEmpty && drawerFooter) {
        if (data.items.length === 0) {
          drawerContainer.innerHTML = '';
          drawerEmpty.classList.remove('d-none');
          drawerFooter.classList.add('d-none');
        } else {
          drawerEmpty.classList.add('d-none');
          drawerFooter.classList.remove('d-none');

          drawerContainer.innerHTML = data.items.map(it => `
            <div class="cart-item-row">
              <img src="${it.image_url || 'https://images.unsplash.com/photo-1546069901-ba9599a7e63c?auto=format&fit=crop&w=150&q=80'}" 
                   alt="${it.name}" class="cart-item-thumb">
              <div class="flex-grow-1">
                <div class="d-flex justify-content-between align-items-start">
                  <h6 class="mb-0 fw-bold">${it.name}</h6>
                  <button type="button" class="btn btn-link text-danger p-0 ms-2 btn-remove-item" data-item-id="${it.id}" title="Remove">
                    <i class="bi bi-trash3"></i>
                  </button>
                </div>
                <div class="text-muted small mb-1">$${it.price} each</div>
                <div class="d-flex justify-content-between align-items-center mt-1">
                  <div class="qty-control">
                    <button type="button" class="qty-btn" data-item-id="${it.id}" data-action="dec">-</button>
                    <span class="qty-val" data-item-id="${it.id}">${it.quantity}</span>
                    <button type="button" class="qty-btn" data-item-id="${it.id}" data-action="inc">+</button>
                  </div>
                  <span class="fw-bold text-dark">$${it.subtotal}</span>
                </div>
              </div>
            </div>
          `).join('');
        }
      }

      // If on checkout page, update the checkout summary items dynamically as well
      const checkoutSummaryList = document.getElementById('checkoutSummaryItems');
      const checkoutSubtotal = document.getElementById('checkoutSubtotal');
      const checkoutTax = document.getElementById('checkoutTax');
      const checkoutTotal = document.getElementById('checkoutTotal');
      const checkoutSubmitBtn = document.getElementById('btnSubmitOrder');

      if (checkoutSummaryList && checkoutSubtotal) {
        checkoutSubtotal.textContent = `$${data.subtotal}`;
        if (checkoutTax) checkoutTax.textContent = `$${data.tax}`;
        if (checkoutTotal) checkoutTotal.textContent = `$${data.grand_total}`;

        if (data.items.length === 0) {
          checkoutSummaryList.innerHTML = `
            <div class="text-center py-4 text-muted">
              <i class="bi bi-cart-x fs-1 d-block mb-2 text-secondary"></i>
              Your cart is empty. Please add items from the menu.
            </div>`;
          if (checkoutSubmitBtn) checkoutSubmitBtn.disabled = true;
        } else {
          if (checkoutSubmitBtn) checkoutSubmitBtn.disabled = false;
          checkoutSummaryList.innerHTML = data.items.map(it => `
            <div class="d-flex justify-content-between align-items-center py-2 border-bottom">
              <div class="d-flex align-items-center gap-2">
                <div class="qty-control">
                  <button type="button" class="qty-btn" data-item-id="${it.id}" data-action="dec">-</button>
                  <span class="qty-val" data-item-id="${it.id}">${it.quantity}</span>
                  <button type="button" class="qty-btn" data-item-id="${it.id}" data-action="inc">+</button>
                </div>
                <span class="fw-semibold">${it.name}</span>
              </div>
              <div class="text-end">
                <span class="fw-bold">$${it.subtotal}</span>
                <button type="button" class="btn btn-link text-danger p-0 ms-2 btn-remove-item" data-item-id="${it.id}">
                  <i class="bi bi-x-circle"></i>
                </button>
              </div>
            </div>
          `).join('');
        }
      }

    } catch (err) {
      console.error('Error fetching cart data:', err);
    }
  }

  updateBadgeCounts(count) {
    const badges = document.querySelectorAll('.cart-count-badge');
    badges.forEach(b => {
      b.textContent = count;
      if (count > 0) {
        b.classList.remove('d-none');
      } else {
        b.classList.add('d-none');
      }
    });
  }

  saveLocalCartCount(count) {
    try {
      localStorage.setItem(this.storageKey, JSON.stringify({ count: count, timestamp: Date.now() }));
    } catch (e) {}
  }

  showToast(type, message) {
    const toastContainer = document.getElementById('toastContainer');
    if (!toastContainer) return;

    const toastEl = document.createElement('div');
    toastEl.className = `toast align-items-center text-white bg-${type === 'danger' ? 'danger' : (type === 'info' ? 'primary' : 'success')} border-0 shadow-lg`;
    toastEl.setAttribute('role', 'alert');
    toastEl.setAttribute('aria-live', 'assertive');
    toastEl.setAttribute('aria-atomic', 'true');

    toastEl.innerHTML = `
      <div class="d-flex">
        <div class="toast-body d-flex align-items-center gap-2">
          <i class="bi ${type === 'danger' ? 'bi-exclamation-triangle-fill' : 'bi-check-circle-fill'}"></i>
          <span>${message}</span>
        </div>
        <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
      </div>
    `;

    toastContainer.appendChild(toastEl);
    if (typeof bootstrap !== 'undefined') {
      const bsToast = new bootstrap.Toast(toastEl, { delay: 3500 });
      bsToast.show();
      toastEl.addEventListener('hidden.bs.toast', () => toastEl.remove());
    }
  }
}

// Instantiate Cart on DOM Load
document.addEventListener('DOMContentLoaded', () => {
  window.restaurantCart = new RestaurantCart();
});
