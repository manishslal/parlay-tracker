/**
 * Bottom Navigation Handler
 * Manages navigation bar functionality and routing
 */

class BottomNavigation {
  constructor() {
    this.navElement = document.querySelector('.bottom-nav');
    this.navItems = document.querySelectorAll('.bottom-nav-item');
    this.init();
  }

  init() {
    if (!this.navElement) return;
    
    this.setupEventListeners();
    this.setActiveByPath();
  }

  setupEventListeners() {
    this.navItems.forEach((item) => {
      item.addEventListener('click', (e) => this.handleNavClick(e, item));
    });
  }

  handleNavClick(e, item) {
    e.preventDefault();
    
    const href = item.getAttribute('href');
    if (!href) return;

    // Update active state
    this.setActive(item);

    // Handle navigation
    const action = item.getAttribute('data-action');
    if (action) {
      this.handleAction(action);
    } else if (href !== '#') {
      window.location.href = href;
    }
  }

  setActive(item) {
    // Remove active from all items
    this.navItems.forEach((navItem) => {
      navItem.classList.remove('active');
    });

    // Add active to current item
    item.classList.add('active');

    // Store in sessionStorage for persistence
    const action = item.getAttribute('data-action') || item.getAttribute('href');
    sessionStorage.setItem('activeNavItem', action);
  }

  setActiveByPath() {
    const currentPath = window.location.pathname;
    const activeNavItem = sessionStorage.getItem('activeNavItem');

    this.navItems.forEach((item) => {
      const href = item.getAttribute('href');
      const action = item.getAttribute('data-action');

      // Match by path
      if (href && currentPath.includes(href.replace(/^\//, ''))) {
        this.setActive(item);
        return;
      }

      // Match by stored action
      if (action && action === activeNavItem) {
        this.setActive(item);
        return;
      }
    });
  }

  handleAction(action) {
    switch (action) {
      case 'my-bets':
        this.navigateToMyBets();
        break;
      case 'explore':
        this.navigateToExplore();
        break;
      case 'watched':
        this.navigateToWatched();
        break;
      case 'social':
        this.navigateToSocial();
        break;
      case 'account':
        this.navigateToAccount();
        break;
      default:
        break;
    }
  }

  navigateToMyBets() {
    window.location.href = '/';
  }

  navigateToExplore() {
    // Navigate to explore page (to be implemented)
    window.location.href = '/explore';
  }

  navigateToWatched() {
    // Navigate to watched page (to be implemented)
    window.location.href = '/watched';
  }

  navigateToSocial() {
    // Navigate to social page (to be implemented)
    window.location.href = '/social';
  }

  navigateToAccount() {
    // Navigate to modern account page
    window.location.href = '/account';
  }

  /**
   * Set badge count on nav item
   * @param {string} action - Nav action (my-bets, explore, etc.)
   * @param {number} count - Badge count to display
   */
  setBadge(action, count) {
    const item = Array.from(this.navItems).find(
      (i) => i.getAttribute('data-action') === action
    );

    if (!item) return;

    let badge = item.querySelector('.nav-badge');

    if (count > 0) {
      if (!badge) {
        badge = document.createElement('span');
        badge.className = 'nav-badge';
        item.appendChild(badge);
      }
      badge.textContent = count > 99 ? '99+' : count;
    } else if (badge) {
      badge.remove();
    }
  }

  /**
   * Show notification on nav item
   * @param {string} action - Nav action
   * @param {boolean} show - Show or hide notification
   */
  setNotification(action, show = true) {
    const item = Array.from(this.navItems).find(
      (i) => i.getAttribute('data-action') === action
    );

    if (!item) return;

    if (show) {
      item.classList.add('notification');
    } else {
      item.classList.remove('notification');
    }
  }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
  window.bottomNav = new BottomNavigation();
});

// Reinitialize on page visibility change (for PWA)
document.addEventListener('visibilitychange', () => {
  if (!document.hidden && window.bottomNav) {
    window.bottomNav.setActiveByPath();
  }
});
