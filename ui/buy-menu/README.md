# Bonus-buy menu (Aki Labs standard)

Reference implementation: `BuyMenuAki.svelte` (Svelte 5, no dependency; copy of grumpy-mole
`packages/components-slot-ui/src/BuyMenuAki.svelte`). Approved by the owner on 2026-11-09 after comparing the Paperclip
menus (Toon Sailor closest): "aller ça me va".

## Layout
- The live game stays behind: backdrop blur 4 px, brightness 0.45, saturation 0.85 (fades in 0.3 s).
- Cards in one row, centred slightly above the middle (landscape, design space 1672 x 941); portrait (941 x 1672):
  two rows of two, bigger cards.
- **Card** (250 design px wide): glass panel, no border, 14 px radius.
  1. full-bleed **banner** 3:2 (game art, see below);
  2. **volatility**: three HUD bolts, gold when on, 16 % white when off;
  3. **name** in capitals ("FUSE BONUS");
  4. **price** for the current bet (25 px);
  5. **BUY** button: full width, violet gradient (social mode: the jurisdiction's word, e.g. GET).
- **Balance / bet bar** docked to the bottom edge of the screen (rounded top corners only): BALANCE, separator,
  [-] BET [+] with the HUD square buttons. Changing the bet re-prices the cards with a bump.
- **Close**: HUD square button top right; Escape and a click outside the cards close too.

## States and motion
- Open: cards rise one after another (60 ms stagger, slight overshoot), the bar slides up from the bottom edge.
- Hover: the card lifts 10 px; its bolts pop one after the other; the button brightens. Nothing else.
- Press: the card scales to 0.98. A card only opens the game's confirmation.
- **Locked** (price above the balance): banner grey and dark, name and bolts at 55 %, price red `--aki-danger`, button
  grey with a lock icon; no lift; a click shakes the card and buys nothing.
- Close: cards drop and fade (0.18 s), the bar slides down, the blur fades out.

## Banners (per game)
- 3:2 landscape, full bleed (no frame, no text, no logo), the bonus object centred and large, the game's own setting
  behind it softer, in the game's painting style. Generated with the ChatGPT bridge using the old card art (object
  design) + a game capture (style) as references; webp, about 750 x 500.

## Confirmation
A card opens the purchase confirmation in the same material (grumpy-mole `Confirm.svelte` with `aki`): veil
rgb(8 5 16 / 0.7), glass panel 360 px without border (14 px radius), the card's banner full width on top, small
uppercase title (CONFIRM), the question ("Buy Fuse for $65.00?"), CANCEL = glass button with the inset rim, CONFIRM =
violet gradient; both 44 px high, 7 px radius.

## Reference game
Grumpy Mole (2026-11-09): banners `public/art/ui/bonus/banner-<mode>.webp`, prompts and generation jobs in
`art-source/buy-cards/jobs/`, live mock-up `art-source/buy-cards/live.html`.
