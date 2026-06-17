# Design System: HJAI

## 1. Visual Theme & Atmosphere
A restrained, cockpit-dense interface with fluid spring-physics motion. The atmosphere is clinical yet sophisticated — like a modern professional IDE or high-end trading terminal, optimized for extended interaction and readability.

## 2. Color Palette & Roles
- **Canvas Zinc** (#FAFAFA) — Primary background surface for light mode (Off-Black #09090B for dark mode).
- **Pure Surface** (#FFFFFF) — Card and container fill (Dark mode: #18181B).
- **Charcoal Ink** (#18181B) — Primary text, Zinc-950 depth (Dark mode: #FAFAFA).
- **Muted Steel** (#71717A) — Secondary text, descriptions, metadata.
- **Whisper Border** (rgba(226,232,240,0.5)) — Card borders, 1px structural lines (Dark mode: rgba(39,39,42,0.5)).
- **Cobalt Accent** (#2563EB) — Single accent for CTAs, active states, focus rings. Max 1 accent. Saturation < 80%. No purple/neon.

## 3. Typography Rules
- **Display:** `Geist` — Track-tight, controlled scale, weight-driven hierarchy.
- **Body:** `Geist` — Relaxed leading, 65ch max-width, neutral secondary color.
- **Mono:** `Geist Mono` — For code blocks, model metadata, timestamps, high-density numbers.
- **Banned:** Inter, generic system fonts for premium contexts. Serif fonts banned in dashboards.

## 4. Component Stylings
* **Buttons:** Flat, no outer glow. Tactile -1px translate on active. Accent fill for primary, ghost/outline for secondary.
* **Cards:** Subtly rounded corners (0.75rem). Diffused whisper shadow. Used only when elevation serves hierarchy. High-density: replace with border-top dividers.
* **Inputs:** Label above, error below. Focus ring in accent color. No floating labels.
* **Loaders:** Skeletal shimmer matching exact layout dimensions. No circular spinners.
* **Empty States:** Composed, illustrated compositions — not just "No data" text.

## 5. Layout Principles
Grid-first responsive architecture. Left-Aligned for Hero/Dashboard sections.
Strict single-column collapse below 768px. Max-width containment (1400px centered) for dashboards.
No flexbox percentage math. Generous internal padding.

## 6. Motion & Interaction
Spring physics for all interactive elements (stiffness: 100, damping: 20). Staggered cascade reveals for chat messages.
Perpetual micro-loops on active dashboard components (e.g., active model status). Hardware-accelerated transforms only.

## 7. Anti-Patterns (Banned)
- No emojis anywhere
- No `Inter` font
- No generic serif fonts
- No pure black (`#000000`)
- No neon glows or AI "purple/blue" cliché styling
- No 3-column equal grids
- No AI copywriting clichés ("Elevate", "Seamless", "Unleash")
- No generic placeholder names
- No broken image links
- No fake/invented system performance metrics
- No centered hero layouts
- No full-height `h-screen` (use `min-h-[100dvh]`)
