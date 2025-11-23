# Styling Best Practices & Component Guide

## CSS Variables Usage

### ✅ DO: Use CSS Variables

```css
/* Good - Using CSS variables */
.card {
  background: var(--surface);
  color: var(--text-primary);
  padding: var(--space-lg);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-md);
}
```

### ❌ DON'T: Hardcode Values

```css
/* Bad - Hardcoded values */
.card {
  background: #252525;
  color: #e0e0e0;
  padding: 24px;
  border-radius: 12px;
  box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}
```

## Responsive Design

### ✅ DO: Mobile-First Approach

```html
<!-- Mobile layout first -->
<div class="grid grid-1">
  <!-- Single column on mobile -->
</div>

<!-- CSS: Desktop override -->
@media (min-width: 768px) {
  .grid-1 { grid-template-columns: repeat(2, 1fr); }
}
```

### ✅ DO: Use Responsive Classes

```html
<!-- Auto-responsive grids -->
<div class="grid grid-2">
  <div class="card">Item 1</div>
  <div class="card">Item 2</div>
  <div class="card">Item 3</div>
  <!-- Becomes 1 column on mobile automatically -->
</div>
```

### ✅ DO: Hide Content Responsively

```html
<!-- Only show on mobile -->
<div class="show-mobile">Mobile Menu</div>

<!-- Only show on desktop -->
<div class="hide-mobile">Desktop Menu</div>
```

## Spacing & Layout

### ✅ DO: Use Utility Classes

```html
<!-- Using spacing utilities -->
<div class="card mt-lg mb-lg px-md py-md">
  <p class="mb-md">Heading</p>
  <p class="text-small">Description</p>
</div>
```

### ❌ DON'T: Inline Styles

```html
<!-- Bad - Inline styles -->
<div style="margin-top: 24px; margin-bottom: 24px; padding-left: 16px; padding-right: 16px;">
  Content
</div>
```

### Spacing Guide

```
Utility Class    Size       Usage
mt-xs           4px        Minimal space
mt-sm           8px        Small space
mt-md           16px       Default space
mt-lg           24px       Large space
mt-xl           32px       Extra large space
mt-2xl          48px       Double large space

Same for: mb-*, px-*, py-*
```

## Typography

### ✅ DO: Use Typography Variables

```html
<!-- Good - Using CSS variable text sizes -->
<h1>Heading 1</h1>        <!-- 30px Bold -->
<h2>Heading 2</h2>        <!-- 24px Bold -->
<h3>Heading 3</h3>        <!-- 20px Bold -->
<p>Body text</p>          <!-- 16px Regular -->
<p class="text-sm">Small</p>  <!-- 14px -->
<p class="text-xs">XS</p>    <!-- 12px -->
```

### Typography Sizes

```
Variable          Size    Weight   Usage
--text-xs         12px    Regular  Small labels
--text-sm         14px    Regular  Helper text
--text-base       16px    Regular  Body text
--text-lg         18px    Regular  Larger text
--text-xl         20px    Regular  Small headings
--text-2xl        24px    Bold     Section headings
--text-3xl        30px    Bold     Page headings

Font Families: --font-family (Roboto), --font-mono (Courier)
Weights: --weight-light (300), --weight-regular (400), 
         --weight-medium (500), --weight-bold (700)
```

### ✅ DO: Maintain Heading Hierarchy

```html
<!-- Correct hierarchy -->
<h1>Page Title</h1>
  <h2>Section Title</h2>
    <h3>Subsection</h3>
      <p>Body text</p>
```

### ❌ DON'T: Skip Heading Levels

```html
<!-- Bad - Skips h2 -->
<h1>Page Title</h1>
<h3>Subsection</h3>  <!-- Should be h2 -->
```

## Color Usage

### ✅ DO: Use Color Variables

```css
/* Good - Using color variables */
.button {
  background: var(--primary);
  color: #ffffff;
  border: 1px solid var(--border-primary);
}

.error-message {
  color: var(--status-error);
  background: rgba(244, 67, 54, 0.1);
}
```

### Color Palette Reference

```
Primary Colors:
  --primary: #140d52 (Purple)
  --secondary: #ff9800 (Orange)
  --tertiary: #ffeb3b (Yellow)
  --accent: #e657ff (Magenta)

Text Colors:
  --text-primary: #e0e0e0 (Main text)
  --text-secondary: #bdbdbd (Secondary)
  --text-tertiary: #9e9e9e (Tertiary)

Status Colors:
  --status-success: #4caf50 (Green)
  --status-warning: #ff9800 (Orange)
  --status-pending: #ffc107 (Yellow)
  --status-error: #f44336 (Red)
  --status-live: #03a9f4 (Blue)
```

## Button Components

### ✅ DO: Use Button Classes

```html
<!-- Primary action -->
<button class="btn btn-primary">Submit</button>

<!-- Secondary action -->
<button class="btn btn-secondary">Next</button>

<!-- Tertiary/Ghost action -->
<button class="btn btn-ghost">Cancel</button>

<!-- Size variations -->
<button class="btn btn-primary btn-small">Small</button>
<button class="btn btn-primary">Normal</button>
<button class="btn btn-primary btn-large">Large</button>

<!-- Disabled state -->
<button class="btn btn-primary" disabled>Disabled</button>
```

### ❌ DON'T: Style Buttons Inline

```html
<!-- Bad - Inline button styling -->
<button style="background: #140d52; color: white; padding: 15px 30px; border-radius: 8px;">
  Submit
</button>
```

### Button Sizes

```
Class              Height   Padding     Font Size
(no size)          44px     0 24px      16px (default)
btn-small          36px     0 16px      14px
btn-large          48px     0 32px      18px
```

## Card Components

### ✅ DO: Use Card Structure

```html
<!-- Proper card structure -->
<div class="card">
  <div class="card-header">
    <h3>Card Title</h3>
    <span class="badge badge-success">Active</span>
  </div>
  <div class="card-body">
    <p>Card content goes here</p>
  </div>
  <div class="card-footer">
    <button class="btn btn-primary btn-small">Action</button>
    <button class="btn btn-ghost btn-small">Cancel</button>
  </div>
</div>
```

### ❌ DON'T: Nested Divs

```html
<!-- Bad - No semantic structure -->
<div class="box" style="padding: 20px; background: #252525; border-radius: 12px;">
  <div style="font-weight: bold; margin-bottom: 10px;">Title</div>
  <div style="margin-bottom: 15px;">Content</div>
  <div style="display: flex; gap: 10px;">
    <button>Action</button>
    <button>Cancel</button>
  </div>
</div>
```

## Table Styling

### ✅ DO: Use Table Wrapper

```html
<!-- Proper table with responsive wrapper -->
<div class="table-wrapper">
  <table>
    <thead>
      <tr>
        <th>Column 1</th>
        <th>Column 2</th>
        <th>Column 3</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>Data 1</td>
        <td>Data 2</td>
        <td>Data 3</td>
      </tr>
    </tbody>
  </table>
</div>
```

### Table Features

```css
/* Automatic styles applied */
- Sticky header
- Hover states
- Responsive scrolling
- Consistent border colors
- Proper padding/spacing
```

## Badge Components

### ✅ DO: Use Status Badges

```html
<!-- Status badges -->
<span class="badge badge-success">✓ Won</span>
<span class="badge badge-warning">⚠ Warning</span>
<span class="badge badge-pending">◉ Pending</span>
<span class="badge badge-error">✕ Lost</span>
<span class="badge badge-info">ℹ Info</span>
```

### Badge Colors

```
badge-success   Green      Successful action/state
badge-warning   Orange     Warning/caution
badge-pending   Yellow     Pending action
badge-error     Red        Error/failed action
badge-info      Blue       Info/live indicator
```

## Form Elements

### ✅ DO: Style Form Inputs

```html
<!-- Proper form styling -->
<div class="form-group">
  <label>Email Address</label>
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

### Form Input Features

```css
/* Auto-applied to input, textarea, select */
- 44px height (touch-friendly)
- Color transitions on focus
- Border color change on focus
- Dark/light mode support
- Consistent font sizing
```

## Grid Layouts

### ✅ DO: Use Responsive Grids

```html
<!-- Auto-responsive grid -->
<div class="grid grid-3">
  <div class="card">Item 1</div>
  <div class="card">Item 2</div>
  <div class="card">Item 3</div>
  <!-- 3 cols desktop → 1 col mobile -->
</div>
```

### Grid Classes

```
grid-2    2 column grid (desktop) → 1 column (mobile)
grid-3    3 column grid (desktop) → 1 column (mobile)
grid-4    4 column grid (desktop) → 1 column (mobile)

Gap: 24px (uses var(--space-lg))
```

## Flexbox Utilities

### ✅ DO: Use Flex Classes

```html
<!-- Basic flex -->
<div class="flex">
  <div>Item 1</div>
  <div>Item 2</div>
</div>

<!-- Column layout -->
<div class="flex flex-col">
  <div>Item 1</div>
  <div>Item 2</div>
</div>

<!-- Centered -->
<div class="flex flex-center">
  <div>Centered content</div>
</div>

<!-- Space between -->
<div class="flex flex-between">
  <div>Left</div>
  <div>Right</div>
</div>
```

## Dark/Light Mode

### ✅ DO: Let CSS Variables Handle It

```html
<!-- No JavaScript needed for color switching -->
<body class="dark-mode">  <!-- Default -->
<body class="light-mode"> <!-- Light version -->
```

The CSS variables automatically adjust colors based on the `body` class.

### ❌ DON'T: Hardcode Different Colors

```css
/* Bad - Separate colors for each mode */
body.dark-mode { color: #e0e0e0; }
body.light-mode { color: #212121; }

/* Good - Single color variable */
p { color: var(--text-primary); }
```

## Accessibility

### ✅ DO: Include Focus States

```css
button:focus {
  outline: 2px solid var(--primary);
  outline-offset: 2px;
}

input:focus {
  outline: none;
  border-color: var(--primary);
  box-shadow: 0 0 0 3px rgba(20, 13, 82, 0.1);
}
```

### ✅ DO: Use Semantic HTML

```html
<!-- Good - Semantic HTML -->
<header>Page Header</header>
<nav>Navigation</nav>
<main>Main Content</main>
<footer>Footer</footer>

<!-- Bad - Generic divs -->
<div id="header">Page Header</div>
<div id="nav">Navigation</div>
<div id="content">Main Content</div>
```

### ✅ DO: Respect Motion Preferences

```css
/* Reduce motion for users who prefer it */
@media (prefers-reduced-motion: reduce) {
  * {
    animation: none !important;
    transition: none !important;
  }
}
```

## Performance Tips

1. **Use CSS variables** instead of calculating in JavaScript
2. **Leverage flexbox/grid** instead of float-based layouts
3. **Use box-shadow variable** instead of creating new shadows
4. **Cache color calculations** with CSS variables
5. **Minimize inline styles** - use utility classes instead
6. **Use CSS transitions** for smooth animations (hardware accelerated)

## Component Checklist

### Before deploying a new component:

- ✅ Uses CSS variables for colors/sizing
- ✅ Has proper spacing (using utility classes)
- ✅ Works on mobile (< 480px)
- ✅ Works on tablet (480-768px)
- ✅ Works on desktop (> 768px)
- ✅ Has focus/hover states
- ✅ Supports dark/light mode
- ✅ Uses semantic HTML
- ✅ Follows heading hierarchy
- ✅ Touch targets are 44px+
- ✅ Respects reduced motion preference
- ✅ Documented with examples

## Quick Reference

```
Typography: h1, h2, h3, h4, p, .text-sm, .text-xs
Buttons: .btn, .btn-primary, .btn-secondary, .btn-ghost, .btn-small, .btn-large
Cards: .card, .card-header, .card-body, .card-footer
Grids: .grid, .grid-2, .grid-3, .grid-4
Flex: .flex, .flex-col, .flex-center, .flex-between
Spacing: .mt-*, .mb-*, .px-*, .py-* (xs/sm/md/lg/xl)
Badges: .badge, .badge-success, .badge-error, .badge-warning, .badge-info
Tables: .table-wrapper, table, thead, tbody, th, td
Forms: input, textarea, select, .form-group, label
Status: .text-success, .text-error, .text-warning, .text-info, .text-muted
```

---

For more details, see `design-system.css` and `DESIGN_SYSTEM_IMPLEMENTATION.md`
