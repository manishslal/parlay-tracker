# Design System Implementation Guide

## Overview

This guide shows how to integrate the new design system into all HTML pages.

## Files Created

### Core Design System Files
1. **design-system.css** - Main design system with:
   - CSS Variables (colors, typography, spacing, sizing, shadows, z-index)
   - Dark/Light mode support
   - Component base classes (buttons, cards, tables, inputs, grids)
   - Responsive utilities
   - Accessibility features

2. **bottom-nav.css** - Bottom navigation bar styling:
   - Fixed positioning at screen bottom
   - 5 nav items with icons and labels
   - Active state indicators
   - Dark/light mode support
   - Responsive adjustments
   - Badge notification support

3. **icons.css** - Icon system:
   - SVG-based scalable icons
   - Data attributes for easy icon usage
   - Support for multiple sizes (xs, sm, md, lg, xl)
   - Dark/light mode compatible
   - Includes: My Bets, Explore, Watched, Social, Account, Home, Settings, Add, and status icons

4. **bottom-nav.js** - Navigation functionality:
   - Auto-initialization on page load
   - Active state management
   - Navigation routing
   - Badge and notification support
   - Session storage for persistence

5. **DESIGN_SYSTEM_TEMPLATE.html** - Reference template showing all components

## Integration Steps

### Step 1: Update HTML Head Section

Add these three lines to the `<head>` section of every HTML file (before page-specific styles):

```html
<!-- Design System Stylesheets -->
<link rel="stylesheet" href="design-system.css">
<link rel="stylesheet" href="bottom-nav.css">
<link rel="stylesheet" href="icons.css">
```

**Files to Update:**
- index.html
- add-bet.html
- admin.html
- login.html

### Step 2: Add Bottom Navigation

Add this HTML before the closing `</body>` tag:

```html
<!-- BOTTOM NAVIGATION BAR -->
<nav class="bottom-nav">
  <a href="/" class="bottom-nav-item" data-action="my-bets">
    <span class="nav-icon">📊</span>
    <span class="nav-label">My Bets</span>
  </a>
  <a href="/explore" class="bottom-nav-item" data-action="explore">
    <span class="nav-icon">🔍</span>
    <span class="nav-label">Explore</span>
  </a>
  <a href="/watched" class="bottom-nav-item" data-action="watched">
    <span class="nav-icon">⭐</span>
    <span class="nav-label">Watched</span>
  </a>
  <a href="/social" class="bottom-nav-item" data-action="social">
    <span class="nav-icon">👥</span>
    <span class="nav-label">Social</span>
  </a>
  <a href="/account" class="bottom-nav-item" data-action="account">
    <span class="nav-icon">👤</span>
    <span class="nav-label">Account</span>
  </a>
</nav>

<script src="bottom-nav.js"></script>
```

### Step 3: Wrap Content in Container

Ensure main page content is wrapped in a container class for proper spacing:

```html
<div class="container">
  <!-- Your page content here -->
</div>
```

This adds padding and ensures content doesn't get hidden behind the fixed bottom nav.

### Step 4: Update Component Classes

Replace or add these classes to improve visual consistency:

#### Buttons
```html
<!-- Old -->
<button>Add Bet</button>

<!-- New -->
<button class="btn btn-primary">Add Bet</button>
<button class="btn btn-secondary">Submit</button>
<button class="btn btn-ghost">Cancel</button>
```

#### Cards/Boxes
```html
<!-- Old -->
<div class="box">Content</div>

<!-- New -->
<div class="card">
  <div class="card-header">
    <h3>Title</h3>
  </div>
  <div class="card-body">
    Content here
  </div>
  <div class="card-footer">
    Footer content
  </div>
</div>
```

#### Headings
```html
<!-- Use standard HTML with consistency -->
<h1>Page Title</h1>
<h2>Section Title</h2>
<h3>Subsection</h3>
```

#### Spacing
```html
<!-- Use utility classes for consistent spacing -->
<div class="mt-lg mb-lg px-md py-md">
  Content with consistent spacing
</div>
```

#### Badges/Status
```html
<!-- Status indicators -->
<span class="badge badge-success">✓ Won</span>
<span class="badge badge-pending">◉ Pending</span>
<span class="badge badge-error">✕ Lost</span>
```

#### Grids
```html
<!-- Responsive layouts -->
<div class="grid grid-2">
  <div class="card">Column 1</div>
  <div class="card">Column 2</div>
</div>

<!-- On mobile: automatically becomes 1 column -->
```

## CSS Variables Reference

### Colors
```css
/* Primary Colors */
--primary: #140d52
--secondary: #ff9800
--tertiary: #ffeb3b
--accent: #e657ff

/* Text Colors */
--text-primary: #e0e0e0 (dark mode)
--text-secondary: #bdbdbd
--text-tertiary: #9e9e9e

/* Status Colors */
--status-success: #4caf50
--status-warning: #ff9800
--status-pending: #ffc107
--status-error: #f44336
--status-live: #03a9f4

/* Background Colors */
--bg: #121212 (dark mode)
--surface: #252525
--surface-variant: #1a1a1a
```

### Typography
```css
/* Font Sizes */
--text-xs: 0.75rem (12px)
--text-sm: 0.875rem (14px)
--text-base: 1rem (16px)
--text-lg: 1.125rem (18px)
--text-xl: 1.25rem (20px)
--text-2xl: 1.5rem (24px)
--text-3xl: 1.875rem (30px)

/* Weights */
--weight-light: 300
--weight-regular: 400
--weight-medium: 500
--weight-bold: 700
```

### Spacing
```css
--space-xs: 0.25rem (4px)
--space-sm: 0.5rem (8px)
--space-md: 1rem (16px)
--space-lg: 1.5rem (24px)
--space-xl: 2rem (32px)
--space-2xl: 3rem (48px)
```

## Icon System Usage

### Using Emoji (Current/Temporary)
The bottom nav currently uses emoji. To replace with proper icons:

```html
<!-- Current (emoji) -->
<span class="nav-icon">📊</span>

<!-- Future (SVG) - Uncomment when icon system is complete -->
<!-- <span class="nav-icon">
  <svg class="icon icon-md"><use xlink:href="#icon-my-bets"/></svg>
</span> -->
```

### Data Attribute Icons
```html
<!-- Status icon before text -->
<p data-icon="success">Operation completed</p>
<p data-icon="error">An error occurred</p>
<p data-icon="warning">Warning message</p>
```

## Dark/Light Mode

The design system automatically supports dark/light mode:

```html
<body class="dark-mode"><!-- Dark mode (default) -->
<body class="light-mode"><!-- Light mode -->
```

All colors automatically adjust based on the class. CSS variables handle the switching.

## Responsive Breakpoints

The design system uses these breakpoints:

```css
Mobile: < 480px
Tablet: 480px - 768px
Desktop: > 768px
```

Classes like `grid-2` and `grid-3` automatically collapse to 1 column on mobile.

Use responsive utilities:
```html
<div class="hide-mobile">Only visible on desktop</div>
<div class="show-mobile">Only visible on mobile</div>
```

## Bottom Navigation API

Use JavaScript to programmatically control the bottom nav:

```javascript
// Set badge count
window.bottomNav.setBadge('my-bets', 5);

// Show notification
window.bottomNav.setNotification('social', true);

// Remove notification
window.bottomNav.setNotification('social', false);

// Manually set active item
window.bottomNav.setActive(element);
```

## Best Practices

1. **Use CSS Variables**: Never hardcode colors, sizes, or spacing. Always use CSS variables.
   ```css
   /* Good */
   color: var(--text-primary);
   padding: var(--space-lg);
   
   /* Bad */
   color: #e0e0e0;
   padding: 24px;
   ```

2. **Semantic HTML**: Use proper heading hierarchy and semantic tags.
   ```html
   <!-- Good -->
   <h1>Page Title</h1>
   <h2>Section</h2>
   <button class="btn btn-primary">Action</button>
   
   <!-- Bad -->
   <div style="font-size: 30px; font-weight: bold;">Page Title</div>
   <div style="font-size: 24px;">Section</div>
   <div class="clickable">Action</div>
   ```

3. **Utility Classes**: Use provided utility classes instead of inline styles.
   ```html
   <!-- Good -->
   <div class="card mt-lg mb-lg">Content</div>
   
   <!-- Bad -->
   <div class="card" style="margin-top: 24px; margin-bottom: 24px;">Content</div>
   ```

4. **Component Consistency**: Use established component classes.
   ```html
   <!-- Good -->
   <button class="btn btn-primary btn-large">Submit</button>
   
   <!-- Bad -->
   <button style="background: #140d52; padding: 20px; height: 48px;">Submit</button>
   ```

5. **Mobile First**: Always consider mobile layout. Test responsive behavior.
   ```html
   <!-- Good - Responsive grid -->
   <div class="grid grid-3">
     <div class="card">Item 1</div>
     <div class="card">Item 2</div>
     <div class="card">Item 3</div>
   </div>
   
   <!-- Bad - Fixed layout -->
   <div style="display: flex; flex-basis: 33%;">
     <div class="card">Item 1</div>
     <div class="card">Item 2</div>
     <div class="card">Item 3</div>
   </div>
   ```

## Migration Checklist

For each HTML file (index.html, add-bet.html, admin.html, login.html):

- [ ] Add design system CSS imports to `<head>`
- [ ] Add bottom navigation HTML before `</body>`
- [ ] Add bottom-nav.js script import
- [ ] Wrap main content in `.container` div
- [ ] Remove redundant inline styles
- [ ] Update button classes to use `.btn` system
- [ ] Update card/box classes to use `.card` system
- [ ] Replace inline spacing with utility classes
- [ ] Test dark/light mode switching
- [ ] Test responsive layout on mobile
- [ ] Test bottom nav navigation
- [ ] Verify all colors use CSS variables
- [ ] Check accessibility (focus states, ARIA labels)

## Troubleshooting

### Bottom nav not appearing
- Ensure `bottom-nav.css` is linked in `<head>`
- Ensure `bottom-nav.js` is loaded before closing `</body>`
- Check browser console for errors

### Styles not applying
- Ensure `design-system.css` is linked before page-specific styles
- Check that CSS variable names are correct
- Verify no inline styles override design system variables

### Responsive not working
- Ensure viewport meta tag is present: `<meta name="viewport" content="width=device-width, initial-scale=1.0">`
- Check that grid classes are used (grid-2, grid-3, grid-4)
- Test in responsive mode (DevTools: Ctrl+Shift+M or Cmd+Shift+M)

### Dark/Light mode not working
- Ensure HTML has `class="dark-mode"` or `class="light-mode"`
- Check that body class is being toggled correctly
- Verify CSS variables are used for all colors

## Future Enhancements

1. **Icon Library**: Replace emoji with Material Icons or Font Awesome
2. **Animated Components**: Add page transitions and animations
3. **Component Library**: Create reusable JS components (modals, dropdowns, tabs)
4. **Theming**: Allow custom color themes
5. **Accessibility**: Add more ARIA labels and keyboard navigation
6. **Performance**: Optimize CSS and implement lazy loading
7. **Documentation**: Generate living styleguide with all components

## Support

For questions or issues:
1. Review the DESIGN_SYSTEM_TEMPLATE.html for examples
2. Check CSS variables in design-system.css
3. Review bottom-nav.js for JavaScript API
4. Test in responsive mode and with different color modes
