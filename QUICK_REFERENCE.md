# Design System - Quick Reference Card

## 🎨 Color Palette

### Dark Mode (Default)
```
Primary:  #140d52 (Purple)     Text:    #e0e0e0 (Light Gray)
Secondary: #ff9800 (Orange)     Secondary: #bdbdbd (Gray)
Tertiary: #ffeb3b (Yellow)      Tertiary: #9e9e9e (Dark Gray)
Accent:   #e657ff (Magenta)

Success:  #4caf50 (Green)
Warning:  #ff9800 (Orange)
Error:    #f44336 (Red)
Info:     #03a9f4 (Blue)

Background: #121212            Border: #ffcc00a4
Surface:    #252525            Surface Variant: #1a1a1a
```

### Light Mode
```
Background: #f5f5f5            Primary: #5e35b1
Surface:    #ffffff            Text: #212121
```

## 📐 Sizing

### Typography
| Class | Size | Weight | Usage |
|-------|------|--------|-------|
| h1 | 30px | Bold | Page title |
| h2 | 24px | Bold | Section heading |
| h3 | 20px | Bold | Subsection |
| h4 | 18px | Medium | Sub-heading |
| p | 16px | Regular | Body text |
| .text-sm | 14px | Regular | Helper text |
| .text-xs | 12px | Regular | Small text |

### Spacing
| Utility | Size | Usage |
|---------|------|-------|
| xs | 4px | Minimal space |
| sm | 8px | Small space |
| md | 16px | Default space |
| lg | 24px | Large space |
| xl | 32px | Extra large |
| 2xl | 48px | Double large |

### Components
| Component | Height | Usage |
|-----------|--------|-------|
| Button | 44px | Normal size |
| Button Small | 36px | Secondary |
| Button Large | 48px | Primary CTA |
| Input | 44px | Touch-friendly |
| Nav | 60px | Fixed bottom |

## 🔘 Buttons

```html
<!-- Primary Action -->
<button class="btn btn-primary">Submit</button>

<!-- Secondary Action -->
<button class="btn btn-secondary">Next</button>

<!-- Tertiary/Cancel -->
<button class="btn btn-ghost">Cancel</button>

<!-- Sizes -->
<button class="btn btn-small">Small</button>
<button class="btn">Normal</button>
<button class="btn btn-large">Large</button>

<!-- States -->
<button class="btn btn-primary" disabled>Disabled</button>
```

## 📦 Cards

```html
<div class="card">
  <div class="card-header">
    <h3>Title</h3>
    <span class="badge badge-success">Active</span>
  </div>
  <div class="card-body">
    Content goes here
  </div>
  <div class="card-footer">
    <button class="btn btn-primary btn-small">Action</button>
  </div>
</div>
```

## 🏷️ Badges

```html
<span class="badge badge-success">✓ Won</span>
<span class="badge badge-warning">⚠ Warning</span>
<span class="badge badge-error">✕ Error</span>
<span class="badge badge-info">ℹ Info</span>
<span class="badge badge-pending">◉ Pending</span>
```

## 📊 Grids

```html
<!-- 2 Column Grid (1 col on mobile) -->
<div class="grid grid-2">
  <div class="card">Item 1</div>
  <div class="card">Item 2</div>
</div>

<!-- 3 Column Grid (1 col on mobile) -->
<div class="grid grid-3">
  <div class="card">Item 1</div>
  <div class="card">Item 2</div>
  <div class="card">Item 3</div>
</div>

<!-- 4 Column Grid (1 col on mobile) -->
<div class="grid grid-4">
  <div class="card">Item 1</div>
  <div class="card">Item 2</div>
  <div class="card">Item 3</div>
  <div class="card">Item 4</div>
</div>
```

## 🎯 Bottom Navigation

### Navigation Items
```
📊 My Bets    → /
🔍 Explore    → /explore
⭐ Watched    → /watched
👥 Social     → /social
👤 Account    → /account
```

### JavaScript API
```javascript
// Set badge count
window.bottomNav.setBadge('my-bets', 5);

// Show notification
window.bottomNav.setNotification('social', true);

// Hide notification
window.bottomNav.setNotification('social', false);
```

## 📱 Responsive Breakpoints

```css
Mobile:  < 480px   (1 column)
Tablet:  480-768px (2 columns)
Desktop: > 768px   (3+ columns, nav hidden)
```

### Utilities
```html
<!-- Only show on mobile -->
<div class="show-mobile">Mobile content</div>

<!-- Only show on desktop -->
<div class="hide-mobile">Desktop content</div>
```

## 🌓 Dark/Light Mode

```html
<!-- Dark mode (default) -->
<body class="dark-mode">

<!-- Light mode -->
<body class="light-mode">
```

All colors automatically adjust - no JavaScript needed!

## 📝 Forms

```html
<div class="form-group">
  <label>Email</label>
  <input type="email" placeholder="Enter email">
</div>

<div class="form-group">
  <label>Select Option</label>
  <select>
    <option>Option 1</option>
    <option>Option 2</option>
  </select>
</div>

<div class="form-group">
  <label>Message</label>
  <textarea placeholder="Enter message..."></textarea>
</div>
```

## 🎨 Flexbox Utilities

```html
<!-- Flex row (default) -->
<div class="flex">
  <div>Item 1</div>
  <div>Item 2</div>
</div>

<!-- Flex column -->
<div class="flex flex-col">
  <div>Item 1</div>
  <div>Item 2</div>
</div>

<!-- Center items -->
<div class="flex flex-center">
  <div>Centered</div>
</div>

<!-- Space between -->
<div class="flex flex-between">
  <div>Left</div>
  <div>Right</div>
</div>
```

## 📏 Spacing Utilities

```html
<!-- Margin Top -->
<div class="mt-xs">4px</div>
<div class="mt-sm">8px</div>
<div class="mt-md">16px</div>
<div class="mt-lg">24px</div>
<div class="mt-xl">32px</div>

<!-- Margin Bottom -->
<div class="mb-xs">...</div>

<!-- Padding X (left/right) -->
<div class="px-md">16px left & right</div>

<!-- Padding Y (top/bottom) -->
<div class="py-lg">24px top & bottom</div>
```

## ✅ Do's and Don'ts

### ✅ DO:
```html
<!-- Use CSS variables -->
<button class="btn btn-primary">Submit</button>

<!-- Use utility classes -->
<div class="mt-lg mb-lg px-md">Content</div>

<!-- Use semantic HTML -->
<h1>Page Title</h1>
<h2>Section Title</h2>

<!-- Use component classes -->
<div class="card">
  <div class="card-header">Header</div>
</div>
```

### ❌ DON'T:
```html
<!-- Don't hardcode colors -->
<button style="background: #140d52;">Submit</button>

<!-- Don't use inline styles -->
<div style="margin-top: 24px; padding: 16px;">Content</div>

<!-- Don't skip heading levels -->
<h1>Title</h1>
<h3>Skip h2</h3>

<!-- Don't create custom styling -->
<div style="border: 1px solid #ffcc00; padding: 20px;">
```

## 🔗 Files Reference

| File | Purpose | Lines |
|------|---------|-------|
| design-system.css | Main design system | 560 |
| bottom-nav.css | Navigation styling | 210 |
| icons.css | Icon definitions | 320 |
| bottom-nav.js | Navigation functionality | 170 |
| DESIGN_SYSTEM_TEMPLATE.html | Component examples | 250+ |
| DESIGN_SYSTEM_IMPLEMENTATION.md | Integration guide | 300+ |
| BOTTOM_NAV_API.md | JavaScript reference | 250+ |
| STYLING_BEST_PRACTICES.md | Best practices | 400+ |
| COMPLETE_SUMMARY.md | Full documentation | 500+ |

## 🚀 Getting Started

### 1. Link Files (in `<head>`)
```html
<link rel="stylesheet" href="design-system.css">
<link rel="stylesheet" href="bottom-nav.css">
<link rel="stylesheet" href="icons.css">
```

### 2. Add Navigation (before `</body>`)
```html
<nav class="bottom-nav">
  <a href="/" class="bottom-nav-item active" data-action="my-bets">
    <span class="nav-icon">📊</span>
    <span class="nav-label">My Bets</span>
  </a>
  <!-- ... other items ... -->
</nav>
<script src="bottom-nav.js"></script>
```

### 3. Use Components
```html
<button class="btn btn-primary">Submit</button>
<div class="card">
  <div class="card-header"><h3>Title</h3></div>
  <div class="card-body">Content</div>
</div>
```

## 📋 Component Checklist

Before deploying:
- ✅ Uses CSS variables (not hardcoded values)
- ✅ Responsive layout (mobile, tablet, desktop)
- ✅ Dark/light mode compatible
- ✅ Focus/hover states
- ✅ Touch targets 44px+
- ✅ Semantic HTML
- ✅ Proper spacing using utilities
- ✅ Heading hierarchy correct

## 🆘 Quick Troubleshooting

**Colors not changing in dark mode?**
- Check CSS variable names are correct
- Verify body class is set (dark-mode/light-mode)
- Check that custom styles don't override variables

**Bottom nav not showing?**
- Verify bottom-nav.css is linked
- Check bottom-nav.js is loaded
- Verify viewport is < 768px (hidden on desktop)

**Spacing looks off?**
- Use utility classes instead of inline styles
- Check container has proper padding
- Verify responsive padding for mobile

**Buttons not responsive?**
- Add .btn class (provides base styling)
- Use btn-small/btn-large for variants
- Ensure parent container is responsive width

---

**Last Updated:** November 23, 2024
**Status:** Ready for Production
**Version:** 2.0.0
