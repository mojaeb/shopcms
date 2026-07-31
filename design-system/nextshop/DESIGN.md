# Design System: NextShop / Lona Center

Semantic DESIGN.md for Stitch-compatible prompting and agent UI work.
See also `design-system/nextshop/MASTER.md` for implementation tokens.

## 1. Visual Theme & Atmosphere

A restrained teal-trust retail interface — slate canvas, soft elevation, Persian RTL typography. Density: Daily App Balanced. Variance: moderate asymmetric hero (slider + banners). Motion: fluid CSS spring-like easing, no cinematic overload.

## 2. Color Palette & Roles

- **Teal Accent** (#0F766E) — Primary CTA, links, focus rings
- **Teal Soft** (#F0FDFA) — Soft surfaces, chip backgrounds
- **Canvas** (#F8FAFC) — Page background with subtle radial atmosphere
- **Pure Surface** (#FFFFFF) — Cards, panels, auth
- **Charcoal Ink** (#0F172A) — Primary text
- **Muted Steel** (#64748B) — Secondary text, hints
- **Whisper Border** (#E2E8F0) — Structural lines
- **Danger** (#DC2626) — Errors, sale badges only

Max one accent. No purple/neon AI gradients. No pure black.

## 3. Typography Rules

- **Display / Body:** IranYekan Fanum + Yekan fallback
- Hierarchy via weight and color, controlled `clamp()` scale
- Prose max ~65ch, line-height 1.65–1.8
- Banned as primary UI: Inter, Rubik-only stacks without FA coverage

## 4. Component Stylings

- **Buttons:** Teal fill primary; ghost outline; white on colored strips. Tactile press (+1px). Min 44px height.
- **Cards:** Soft radius 16–20px, slate-tinted shadow, hover lift ≤2px
- **Inputs:** Label above, hint optional, error below. Soft teal focus ring
- **Loaders:** Skeleton shimmer matching layout — no spinner-only walls
- **Empty states:** Icon + title + short help + one CTA

## 5. Layout Principles

- Max width 1280px centered
- Asymmetric home hero; trust strip 2×2 / 4-col
- Mid banners prefer 2-column asymmetric over equal 3-card rows
- Single-column collapse below 768px; no page horizontal scroll
- Full-height sections use min-height with `dvh` where needed

## 6. Motion & Interaction

- Ease: cubic-bezier(0.22, 1, 0.36, 1)
- 150–280ms micro/UI; stagger grid reveals ≤200ms delay steps
- Animate transform/opacity only
- Honor prefers-reduced-motion

## 7. Anti-Patterns (Banned)

- Emoji icons (Lucide only)
- Inter as primary font
- Pure black #000
- Neon outer glows / AI purple-pink
- Fabricated metrics / fake SLAs
- AI copy clichés and «Scroll to explore» filler
- Hover-only critical actions
- Removing focus outlines
