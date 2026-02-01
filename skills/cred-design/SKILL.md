---
name: cred-design
description: Create premium, dark-themed frontend interfaces following CRED's distinctive fintech aesthetic. This skill should be used when the user asks to build web components, pages, or applications that need a luxury, dark-first design with editorial typography, high contrast, and refined minimalism.
---

This skill guides creation of frontend interfaces following CRED's premium fintech aesthetic—a dark-first, luxury design language characterized by editorial typography, dramatic contrast, and refined minimalism. Implement real working code with meticulous attention to the CRED design system.

The user provides frontend requirements: a component, page, application, or interface to build. Apply the CRED aesthetic consistently throughout.

## Design Philosophy

CRED's design language embodies **crafted exclusivity**—interfaces that feel premium, intentional, and membership-worthy. Key principles:

- **Dark-first**: Pure black backgrounds create depth and luxury
- **High contrast**: White typography on black creates dramatic impact
- **Editorial typography**: Serif display fonts paired with clean sans-serif body text
- **Generous whitespace**: Spacious layouts that breathe
- **Subtle sophistication**: Restrained animations, muted accents, refined details

## Color System

### Primary Palette
```css
:root {
  --bg-primary: #000000;
  --bg-secondary: #0d0d0d;
  --bg-tertiary: #111111;
  --bg-elevated: #131313;

  --text-primary: #ffffff;
  --text-secondary: rgba(255, 255, 255, 0.7);
  --text-tertiary: rgba(255, 255, 255, 0.45);
  --text-muted: rgba(255, 255, 255, 0.25);

  --border-subtle: #4a4949;
  --border-gradient: linear-gradient(to right, #000, #4a4949, #000);
}
```

### Accent Colors (Use Sparingly)
Vibrant gradients appear only in product imagery and hero visuals:
- Magenta/Pink glows: `#ff00ff` to `#ff66cc`
- Cyan/Teal accents: `#00ffff` to `#00cc99`
- These should NOT be used for UI elements—reserve for imagery and illustrations

## Typography

### Font Stack
```css
/* Primary sans-serif - body text, labels, buttons */
font-family: 'Gilroy', -apple-system, BlinkMacSystemFont, sans-serif;

/* Display serif - hero headlines, section titles */
font-family: 'PP Cirka', 'SwearDisplay', Georgia, serif;

/* Monospace - data, numbers, codes */
font-family: 'Overpass Mono', 'SF Mono', monospace;
```

### Typography Scale
- **Hero headlines**: 48-72px, serif, normal weight
- **Section headers**: 14-16px, ALL CAPS, letter-spacing: 0.15-0.2em, Gilroy Medium
- **Card titles**: 24-32px, serif or sans-serif depending on context
- **Body text**: 16-18px, Gilroy Regular, line-height: 1.6
- **Labels/Tags**: 12-14px, ALL CAPS, letter-spacing: 0.1em
- **Small text**: 14px, opacity 0.6-0.7

### Typography Patterns
```css
/* Hero headline */
.hero-headline {
  font-family: 'PP Cirka', serif;
  font-size: clamp(2.5rem, 5vw, 4.5rem);
  font-weight: 400;
  line-height: 1.1;
  color: var(--text-primary);
}

/* Section label */
.section-label {
  font-family: 'Gilroy', sans-serif;
  font-size: 0.875rem;
  font-weight: 500;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  color: var(--text-primary);
}

/* Body text with reduced opacity */
.body-text {
  font-family: 'Gilroy', sans-serif;
  font-size: 1rem;
  font-weight: 400;
  line-height: 1.6;
  color: var(--text-secondary);
}
```

## Component Patterns

### Cards
- Background: `#000` or subtle gradient
- Border: 1px solid with gradient or subtle gray (`#4a4949`)
- No border-radius (sharp edges preferred)
- Generous padding: 24-32px

```css
.card {
  background: var(--bg-primary);
  border: 1px solid var(--border-subtle);
  padding: 1.5rem 2rem;
}

.card-gradient-border {
  background: var(--bg-primary);
  border-width: 1px;
  border-style: solid;
  border-image: linear-gradient(to right, #000, #4a4949, #000) 1;
}
```

### Buttons
- Outlined style with arrow indicator
- ALL CAPS text with letter-spacing
- No border-radius or minimal (2-4px)
- Hover: subtle background fill or opacity change

```css
.btn-primary {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  background: transparent;
  border: 1px solid var(--text-primary);
  color: var(--text-primary);
  font-family: 'Gilroy', sans-serif;
  font-size: 0.75rem;
  font-weight: 500;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  cursor: pointer;
  transition: background 0.2s ease;
}

.btn-primary:hover {
  background: rgba(255, 255, 255, 0.1);
}

.btn-primary::after {
  content: '→';
}
```

### Navigation
- Vertical menu layouts for expanded states
- Horizontal for header nav
- Dividers between items (gradient or solid)
- ALL CAPS labels

```css
.nav-item {
  font-family: 'Gilroy', sans-serif;
  font-size: 0.875rem;
  font-weight: 500;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--text-secondary);
  padding: 1rem 0;
  border-bottom: 1px solid var(--border-subtle);
  transition: color 0.2s ease;
}

.nav-item:hover,
.nav-item.active {
  color: var(--text-primary);
}
```

### Footer Links
- Multi-column grid layout
- Section headers: uppercase, full opacity
- Links: reduced opacity (0.6-0.7), hover to full

```css
.footer-section-title {
  font-size: 0.75rem;
  font-weight: 600;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  color: var(--text-primary);
  margin-bottom: 1rem;
}

.footer-link {
  font-size: 0.875rem;
  color: var(--text-tertiary);
  text-decoration: none;
  transition: color 0.2s ease;
}

.footer-link:hover {
  color: var(--text-primary);
}
```

## Layout & Spacing

### Section Padding
- Desktop: 100-180px vertical padding
- Tablet: 80px vertical padding
- Mobile: 60-75px vertical padding
- Horizontal: 100-150px desktop, 40px tablet, 15-20px mobile

```css
.section {
  padding: 100px 150px;
}

@media (max-width: 1024px) {
  .section {
    padding: 80px 40px;
  }
}

@media (max-width: 768px) {
  .section {
    padding: 60px 20px;
  }
}
```

### Grid Patterns
- Full-bleed hero sections
- Horizontal scrolling card carousels
- Multi-column footer grids
- Asymmetric layouts for visual interest

## Visual Effects

### Gradients
```css
/* Subtle background gradient */
.gradient-bg {
  background: linear-gradient(90deg, #000, #131313, #000);
}

/* Radial depth */
.radial-bg {
  background: radial-gradient(63.85% 195.77% at 50.93% 100%, #111 0%, #000 100%);
}

/* Border gradient */
.gradient-border {
  border-image: linear-gradient(to right, #000, #4a4949, #000) 1;
}
```

### Micro-interactions
- Subtle opacity transitions (0.2-0.3s ease)
- Hover states that increase text/element opacity
- Flip animations on specific text elements
- Jitter/shake effects on icons (sparingly)

```css
/* Flip text animation */
@keyframes flip {
  0% { transform: rotateX(0deg); opacity: 1; }
  50% { transform: rotateX(180deg); opacity: 0; }
  100% { transform: rotateX(0deg); opacity: 1; }
}

.flip-text:hover span {
  display: inline-block;
  animation: flip 0.7s ease;
}
```

## Implementation Guidelines

1. **Always start with black**: Default background is `#000`, not dark gray
2. **Typography hierarchy through opacity**: Use 100%, 70%, 45%, 25% opacity levels
3. **Minimal color**: Accent colors only in imagery, not UI chrome
4. **Sharp edges**: Avoid border-radius unless specifically needed
5. **Generous space**: When in doubt, add more padding
6. **ALL CAPS for labels**: Section headers, buttons, navigation items
7. **Serif for impact**: Use serif fonts for hero headlines and key statements
8. **Subtle borders**: Gray borders (`#4a4949`) or gradient borders, never stark white

## Anti-patterns to Avoid

- Colored backgrounds (keep everything black/near-black)
- Rounded corners on cards and buttons
- Colorful button fills (use outline style)
- Tight spacing (CRED uses generous whitespace)
- Mixed case for labels (use ALL CAPS)
- Sans-serif for hero headlines (use serif for editorial feel)
- Bright accent colors in UI elements (reserve for imagery only)
- Generic fonts (Inter, Roboto, Arial)

## Font Loading

For web projects, load Gilroy as the primary font. If unavailable, use these alternatives:
- **Sans-serif fallback**: `-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif`
- **Serif alternative**: `Georgia, 'Times New Roman', serif` (for display text)
- **For Google Fonts**: Consider `DM Sans` or `Plus Jakarta Sans` as Gilroy alternatives

```html
<!-- Example with Google Fonts alternatives -->
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=DM+Serif+Display&family=Overpass+Mono:wght@400;500&display=swap" rel="stylesheet">
```
