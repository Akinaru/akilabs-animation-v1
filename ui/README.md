# Aki Labs: in-game UI standard

Every Aki Labs slot shares one UI language, set by the studio HUD (first built on Grumpy Mole, November 2026). Game
art (symbols, plates, banners) changes per game; the UI material does not.

## Material (`tokens.css`)
- **Panels and cards**: dark glass `--aki-glass`, **no border**, 14 px radius, soft drop shadow.
- **Square buttons** (close, - / +, autoplay, turbo): glass, 12 % radius, 1.5 px inset rim `--aki-rim`. Hover: brightness
  1.18. Press: scale 0.92. Disabled: 40 % opacity.
- **Primary action** (buy, bonus): violet gradient `--aki-violet-hi`, 7 px radius, no rim.
- **Type**: Inter 800. Labels small, uppercase, 0.08 em tracking, 70 % opacity. Values large, tabular figures.
  A value that changes bumps (scale 1.12 for 0.25 s).
- **Icons**: the HUD's own SVG icons (single flat colour, no outline, no emoji). Bolt path:
  `M13.5 3 6 13.5h5.5L10.5 21 18 10.5h-5.5Z`.

## Components
- `buy-menu/`: the bonus-buy menu (studio standard). See its README.

## Owner rules (what was refused, so it is not proposed again)
- No painted frame / title plank around studio menus ("fait trop IA"): the live game behind, blurred and dimmed, is
  the frame.
- No border on panels and cards; no pill shapes; no large rounding.
- No emoji icons; no outlines on icons.
- No hover gloss / zoom on illustrations; hover = the card lifts, nothing else.
- Keep cards minimal: no "VOLATILITY" word, no cost multiplier ("65x bet"), no extra tags.
