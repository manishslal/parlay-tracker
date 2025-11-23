# Bottom Navigation JavaScript API

## Quick Reference

The bottom navigation is automatically initialized on page load. You can access it via `window.bottomNav`.

## Basic Usage

### Get the Navigation Instance

```javascript
const nav = window.bottomNav;
```

### Set Active Item

Manually set which bottom nav item is active:

```javascript
// Set by action name
const item = document.querySelector('[data-action="my-bets"]');
window.bottomNav.setActive(item);
```

### Set Badge Count

Display a badge with a count on a nav item:

```javascript
// Show badge with count
window.bottomNav.setBadge('my-bets', 5);      // Shows "5"
window.bottomNav.setBadge('my-bets', 99);     // Shows "99"
window.bottomNav.setBadge('my-bets', 105);    // Shows "99+" (capped)

// Remove badge
window.bottomNav.setBadge('my-bets', 0);      // Removes badge
```

### Show/Hide Notifications

Show a notification indicator on a nav item:

```javascript
// Show notification (red dot)
window.bottomNav.setNotification('social', true);

// Hide notification
window.bottomNav.setNotification('social', false);
```

## Available Actions

The following actions are available for nav items:

- `my-bets` - Route to `/` (main dashboard)
- `explore` - Route to `/explore`
- `watched` - Route to `/watched`
- `social` - Route to `/social`
- `account` - Route to `/account`

## Examples

### Update badge when new bets arrive

```javascript
// Fetch new bets and update badge
fetch('/api/bets?status=live')
  .then(r => r.json())
  .then(data => {
    window.bottomNav.setBadge('my-bets', data.length);
  });
```

### Show notification when user has messages

```javascript
// Check for new social messages
fetch('/api/social/messages?unread=true')
  .then(r => r.json())
  .then(data => {
    window.bottomNav.setNotification('social', data.length > 0);
  });
```

### Auto-update on intervals

```javascript
// Check for updates every 30 seconds
setInterval(() => {
  // Update badges and notifications
  fetch('/api/bets/live')
    .then(r => r.json())
    .then(data => {
      window.bottomNav.setBadge('my-bets', data.length);
    });
  
  fetch('/api/social/unread')
    .then(r => r.json())
    .then(data => {
      const unreadCount = data.messages + data.notifications;
      window.bottomNav.setNotification('social', unreadCount > 0);
    });
}, 30000);
```

## CSS Classes

### Active State

When a nav item is active, it gets the `.active` class:

```html
<a class="bottom-nav-item active" data-action="my-bets">
  <span class="nav-icon">📊</span>
  <span class="nav-label">My Bets</span>
</a>
```

### Styling Active State

```css
.bottom-nav-item.active {
  color: var(--primary);
}

.bottom-nav-item.active::before {
  /* Shows dot indicator above item */
  content: '';
  position: absolute;
  top: 0;
  width: 4px;
  height: 4px;
  background: var(--primary);
}
```

### Badge Element

Badges are automatically created and removed:

```html
<span class="nav-badge">5</span>
```

## Responsive Behavior

### Mobile (< 768px)
- Bottom nav is visible
- Full 5 items displayed
- Height: 56-60px depending on viewport
- Icons: 20-24px
- Labels: 10-12px font

### Desktop (> 768px)
- Bottom nav is hidden (display: none)
- Can be overridden per-page if needed

## Session Storage

The active nav item is stored in sessionStorage for persistence:

```javascript
// Manually check stored value
const active = sessionStorage.getItem('activeNavItem');

// Manually set stored value
sessionStorage.setItem('activeNavItem', 'my-bets');
```

This allows the nav state to persist during navigation and page reloads.

## Event Handling

### Click Handling

The nav automatically handles clicks on items:

```javascript
// Clicking an item with data-action triggers navigation
<a class="bottom-nav-item" data-action="explore" href="/explore">
```

### Programmatic Navigation

Navigate without clicking:

```javascript
// Manually trigger navigation action
window.bottomNav.handleAction('explore');
```

## Troubleshooting

### Bottom nav not appearing

1. Check that `bottom-nav.css` is linked in `<head>`
2. Verify `bottom-nav.js` is loaded before closing `</body>`
3. Check browser console for errors
4. Verify viewport is < 768px (nav hidden on desktop)

### Badge not showing

```javascript
// Make sure count is > 0
window.bottomNav.setBadge('my-bets', 0);  // Removes badge
window.bottomNav.setBadge('my-bets', 1);  // Shows badge
```

### Active state not updating

```javascript
// Ensure page path matches href or action
// Or manually set active state
const item = document.querySelector('[data-action="my-bets"]');
window.bottomNav.setActive(item);
```

### Notification not showing

```javascript
// Use setNotification() instead of setBadge() for notification dots
window.bottomNav.setNotification('social', true);
```

## Integration Example

Complete example showing all features:

```html
<!DOCTYPE html>
<html>
<head>
  <link rel="stylesheet" href="design-system.css">
  <link rel="stylesheet" href="bottom-nav.css">
  <link rel="stylesheet" href="icons.css">
</head>
<body>
  <div class="container">
    <!-- Your page content -->
  </div>
  
  <!-- Bottom Nav -->
  <nav class="bottom-nav">
    <a href="/" class="bottom-nav-item active" data-action="my-bets">
      <span class="nav-icon">📊</span>
      <span class="nav-label">My Bets</span>
    </a>
    <a href="/social" class="bottom-nav-item" data-action="social">
      <span class="nav-icon">👥</span>
      <span class="nav-label">Social</span>
    </a>
  </nav>
  
  <script src="bottom-nav.js"></script>
  
  <script>
    // Wait for bottom nav to initialize
    document.addEventListener('DOMContentLoaded', () => {
      // Update badges
      window.bottomNav.setBadge('my-bets', 3);
      window.bottomNav.setBadge('social', 1);
      
      // Set notifications
      window.bottomNav.setNotification('social', true);
      
      // Refresh every 30 seconds
      setInterval(() => {
        fetch('/api/status')
          .then(r => r.json())
          .then(data => {
            window.bottomNav.setBadge('my-bets', data.liveBets);
            window.bottomNav.setNotification('social', data.hasMessages);
          });
      }, 30000);
    });
  </script>
</body>
</html>
```

## Best Practices

1. **Always check for window.bottomNav** before using it:
   ```javascript
   if (window.bottomNav) {
     window.bottomNav.setBadge('my-bets', count);
   }
   ```

2. **Use data-action for navigation routing** (set in HTML):
   ```html
   <a data-action="my-bets" href="/">My Bets</a>
   ```

3. **Initialize badges/notifications after page load**:
   ```javascript
   document.addEventListener('DOMContentLoaded', () => {
     window.bottomNav.setBadge('my-bets', 5);
   });
   ```

4. **Update nav state when data changes**:
   ```javascript
   fetch('/api/live-bets')
     .then(r => r.json())
     .then(data => {
       window.bottomNav.setBadge('my-bets', data.length);
     });
   ```

5. **Test responsive behavior**:
   - Test on mobile (< 768px)
   - Verify icons and labels are readable
   - Check touch targets are 44px+ height
