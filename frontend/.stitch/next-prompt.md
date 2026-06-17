---
page: chat-interface
---
A highly sophisticated Chat Interface for the HJAI platform. This is the main engine where users interact with the autonomous agents.

**DESIGN SYSTEM (REQUIRED):**
- **Canvas Zinc** (#FAFAFA) — Primary background surface for light mode (Off-Black #09090B for dark mode).
- **Pure Surface** (#FFFFFF) — Card and container fill (Dark mode: #18181B).
- **Charcoal Ink** (#18181B) — Primary text, Zinc-950 depth (Dark mode: #FAFAFA).
- **Muted Steel** (#71717A) — Secondary text, descriptions, metadata.
- **Whisper Border** (rgba(226,232,240,0.5)) — Card borders, 1px structural lines (Dark mode: rgba(39,39,42,0.5)).
- **Cobalt Accent** (#2563EB) — Single accent for CTAs, active states, focus rings. Max 1 accent. Saturation < 80%. No purple/neon.
- **Typography:** `Geist` and `Geist Mono`

**Page Structure:**
1. Header: Simple minimal header saying "Cockpit / Chat Engine"
2. Chat History: A staggered list of messages. User messages are right-aligned with Cobalt Accent backgrounds. Assistant messages are left-aligned with Zinc-900 backgrounds and mono font for code.
3. Input Area: A sleek, modern text input with a right-aligned submit icon. The input should have a subtle border and glow on focus.
