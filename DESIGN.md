# DESIGN.md

## Surface
`themes/minimal` — Persuade on home, Operate on catalog/cart/checkout.

## Color strategy
Restrained neutrals + one signal accent for sale.
- Ink: `#141414`
- Soft ink: `#3f3f46`
- Mute: `#71717a`
- Line: `#e4e4e7`
- Soft: `#f4f4f5`
- Paper: `#ffffff`
- Sale: `#db1215`

## Type
IRANYekan. Display weight 400–500. Body 14px / 1.6. Tracking floor -0.03em on large titles. More space above headings than below.

## Layout
Container `1320px`. Sharp corners (`0`). Hairline borders. Product cards `3/4`. Section rhythm `64–80px` vertical.

## Components
- Header: sticky paper, logo / nav / icon actions, expandable search
- Product card: image hover scale, delayed action reveal, sale badge
- Buttons: solid ink, outline variant, `:active` press scale
- Hero: full-bleed tonal field, brand + one line + one CTA group

## Motion
Tokens:
- `--ease-out: cubic-bezier(0.23, 1, 0.32, 1)`
- `--ease-move: cubic-bezier(0.77, 0, 0.175, 1)`
Durations: press `120ms`, hover `180–220ms`, panel `220ms`. Animate `transform`/`opacity` only. Respect `prefers-reduced-motion`.

## Banned
Eyebrow/kicker labels. Bounce/elastic easing. `transition: all`. `scale(0)` entrances. Pure `#000` fills when tinted ink works.
