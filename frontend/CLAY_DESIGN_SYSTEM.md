# Design System Inspired by Clay

> Category: Design & Creative
> Creative agency. Organic shapes, soft gradients, art-directed layout.

## 1. Visual Theme & Atmosphere

Clay's website is a warm, playful celebration of color that treats B2B data enrichment like a craft rather than an enterprise chore. The design language is built on a foundation of warm cream backgrounds (#faf9f7) and oat-toned borders (#dad4c8, #eee9df) that give every surface the tactile quality of handmade paper. Against this artisanal canvas, a vivid swatch palette explodes with personality — Matcha green, Slushie cyan, Lemon gold, Ube purple, Pomegranate pink, Blueberry navy, and Dragonfruit magenta.

Key Characteristics:
- Warm cream canvas (#faf9f7) with oat-toned borders (#dad4c8)
- Named swatch palette: Matcha, Slushie, Lemon, Ube, Pomegranate, Blueberry, Dragonfruit
- Roobert font with 5 OpenType stylistic sets
- Playful hover animations: rotateZ(-8deg) + translateY(-80%) + hard offset shadow
- Space Mono for code and technical labels
- Generous border radius: 24px cards, 40px sections, 1584px pills
- Mixed border styles: solid + dashed in the same interface
- Multi-layer shadow with inset highlight: 0px 1px 1px + -1px inset + -0.5px

## 2. Color Palette & Roles

### Primary
- Clay Black (#000000)
- Pure White (#ffffff)
- Warm Cream (#faf9f7): Page background

### Swatch Palette
- Matcha 300 (#84e7a5), Matcha 600 (#078a52), Matcha 800 (#02492a)
- Slushie 500 (#3bd3fd), Slushie 800 (#0089ad)
- Lemon 400 (#f8cc65), Lemon 500 (#fbbd41), Lemon 700 (#d08a11), Lemon 800 (#9d6a09)
- Ube 300 (#c1b0ff), Ube 800 (#43089f), Ube 900 (#32037d)
- Pomegranate 400 (#fc7981)
- Blueberry 800 (#01418d)

### Neutral Scale (Warm)
- Warm Silver (#9f9b93), Warm Charcoal (#55534e), Dark Charcoal (#333333)

### Surface & Border
- Oat Border (#dad4c8)
- Oat Light (#eee9df)
- Cool Border (#e6e8ec)
- Dark Border (#525a69)
- Light Frost (#eff1f3)

## 3. Shadows & Depth
- Flat (Level 0): No shadow, cream canvas
- Clay Shadow (Level 1): rgba(0,0,0,0.1) 0px 1px 1px, rgba(0,0,0,0.04) 0px -1px 1px inset, rgba(0,0,0,0.05) 0px -0.5px 1px
- Hover Hard (Level 2): rgb(0,0,0) -7px 7px
- Focus (Level 3): rgb(20, 110, 245) solid 2px

## 4. Components

### Buttons
- Hover animation: rotateZ(-8deg), translateY(-80%), hard shadow rgb(0,0,0) -7px 7px.

### Cards
- Radius: 12px (standard), 24px (feature).
- Border: 1px solid #dad4c8.

*Note: This file is the source of truth for UI/UX elements in Yatra AI Frontend.*
