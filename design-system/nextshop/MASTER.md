# Design System Master File — NextShop (Lona Center)

> Source of truth for `themes/nextshop`. Combines **UI UX Pro Max** (Trust & Authority + Soft UI Evolution) with **Stitch taste-design** anti-generic rules, adapted for Persian RTL retail.

**Project:** NextShop / Lona Center  
**Pattern:** Trust & Authority + Conversion  
**Style:** Soft UI Evolution (accessible soft depth)  
**Stack:** Django templates + CSS + Alpine + Lucide  
**Brand accent:** Teal trust retail (`#0f766e`) — not pharmacy green neon, not AI purple

---

## 1. Visual Theme & Atmosphere

A calm, retail-trust storefront: slate neutrals, one teal accent, soft elevation, and restrained motion. Density sits at **Daily App Balanced (5)**. Variance is moderate — asymmetric hero (slider + banners), not centered marketing hero. Motion is fluid CSS (150–300ms), never cinematic overload.

Keep **IranYekan** (Fanum) for Persian body/digits. **Yekan** is display fallback. Do not switch to Rubik/Nunito/Inter for body text (poor FA coverage).

## 2. Color Palette & Roles

| Role | Hex | Token |
|------|-----|-------|
| Teal Accent (primary) | `#0F766E` | `--primary-600` / `--color-primary` |
| Teal Soft | `#F0FDFA` | `--primary-50` |
| Teal Mid | `#14B8A6` | `--primary-500` |
| Teal Deep | `#115E59` | `--primary-700` |
| Canvas | `#F8FAFC` | `--bg` |
| Surface | `#FFFFFF` | `--card` |
| Charcoal Ink | `#0F172A` | `--text` |
| Muted Steel | `#64748B` | `--muted` |
| Whisper Border | `#E2E8F0` | `--border` |
| Destructive | `#DC2626` | `--danger` |
| Focus ring | `#0F766E` | `--color-ring` |

**Notes:** One accent only. Saturation restrained. Shadows tinted to slate (`rgba(15,23,42,…)`), never neon glow. No purple/pink AI gradients.

## 3. Typography

- Body / UI: **IranYekan** Fanum + **Yekan** fallback
- Display titles: weight 700–800, track slightly tight, scale via `clamp()`
- Body: 400/500, line-height 1.6–1.75, max ~65ch on prose
- Banned for UI chrome: Inter, generic system-only stacks as primary

## 4. Spacing & Radius (Density 5)

`--space-xs` 4px · `--space-sm` 8px · `--space-md` 16px · `--space-lg` 24px · `--space-xl` 32px · `--space-2xl` 48px  
Radius: 12 / 16 / 20px. Cards use soft UI radius, not pill overload.

## 5. Motion

- Ease: `cubic-bezier(0.22, 1, 0.36, 1)` (spring-like)
- Micro: 150ms · UI: 200–250ms · Reveal: ≤400ms
- Animate only `transform` / `opacity`
- Respect `prefers-reduced-motion: reduce`
- Active buttons: tactile `translateY(1px)` press — no outer neon glow

## 6. Shadows (Soft UI Evolution)

- sm: `0 1px 2px rgba(15,23,42,.05)`
- md: `0 4px 12px rgba(15,23,42,.07)`
- lg: `0 12px 28px rgba(15,23,42,.1)`

## 7. Component Rules

- **Buttons:** Primary teal fill; ghost outline; white on colored strips. Min height 44px. `cursor: pointer`.
- **Cards:** Elevation only when hierarchy needs it. Hover lift ≤2px + image scale ≤1.03.
- **Inputs:** Label above, error below. Focus ring 3px soft teal mix.
- **Icons:** Lucide SVG only — never emoji icons.
- **Empty / loading:** Composed empty states + skeleton shimmer — not bare “در حال بارگذاری...” text walls.
- **Trust:** Real assurances only (shipping, SSL, authenticity) — no fabricated metrics.

## 8. Layout

- Max content width ~1280px
- Hero: asymmetric grid (slider + side banners) — not centered landing hero
- Avoid equal 3-column feature rows as the only pattern; prefer 2/4 trust strip or zig-zag sections
- Mobile (<768): single column, no horizontal page scroll
- Touch targets ≥44px; gaps ≥8px between interactive chips

## 9. UX Checklist (must)

- [ ] Lucide SVG icons only
- [ ] `cursor: pointer` on clickable elements
- [ ] Hover feedback 150–300ms
- [ ] Visible `:focus-visible` rings
- [ ] Contrast ≥ 4.5:1 body text
- [ ] Touch targets ≥ 44px where practical
- [ ] `prefers-reduced-motion`
- [ ] Responsive 375 / 768 / 1024 / 1440
- [ ] Skip link to main content
- [ ] Lazy-load below-fold images

## 10. Anti-patterns (Banned)

- AI purple/pink gradients, neon outer glows
- Pure black `#000000`
- Inter as primary UI font
- Emoji as icons
- Fake stats / uptime / invented KPIs
- AI copy clichés («Elevate», «Seamless», «Unleash», «Next-Gen»)
- Filler UI («Scroll to explore», bouncing chevrons)
- Hover-only critical actions
- Removing focus outlines
- Oversized motion (>500ms) on micro UI
- Flat cards with no depth hierarchy on product grids
