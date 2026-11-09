<script lang="ts" module>
  export interface BuyCard {
    mode: string;
    /** Card name, shown in capitals (e.g. "Fuse Bonus"). */
    name: string;
    /** Full-bleed banner art (3:2), game asset. */
    banner: string;
    /** Price for the current bet, formatted. */
    price: string;
    /** Volatility 1..3 (bolts). */
    volatility: number;
    /** Not enough balance for this price: greyed, lock on the button, a click only shakes the card. */
    locked?: boolean;
  }
</script>

<script lang="ts">
  /**
   * Aki Labs studio bonus-buy menu (studio standard, aki-labs-brand/ui/buy-menu): the live game stays behind, blurred
   * and dimmed; one row of cards (portrait: two rows of two), each a HUD glass panel with a full-bleed banner,
   * volatility bolts, name, price and the buy button; the balance / bet bar docked at the bottom of the screen with the
   * HUD's - / + buttons; the HUD's square close button top right. Same material as HudAki: dark glass panels without a
   * border, 14 px radius, square buttons at 12 % radius with the 1.5 px inset rim, violet gradients, Inter 800.
   * A card only opens the confirmation (onpick); a locked card shakes.
   */
  let {
    cards,
    action,
    balance,
    bet,
    labels,
    betDownDisabled = false,
    betUpDisabled = false,
    disabled = false,
    onpick,
    onbet,
    onclose,
  }: {
    cards: BuyCard[];
    action: string;
    balance: string;
    bet: string;
    labels: {balance: string; bet: string; close: string; betDown: string; betUp: string; title: string};
    betDownDisabled?: boolean;
    betUpDisabled?: boolean;
    disabled?: boolean;
    onpick: (c: BuyCard) => void;
    onbet: (dir: -1 | 1) => void;
    onclose: () => void;
  } = $props();

  let vw = $state(1600);
  let vh = $state(900);
  const portrait = $derived(vh > vw);
  /** Design space: 1672 x 941 landscape, 941 x 1672 portrait (the game's scene spaces). */
  const k = $derived(portrait ? Math.min(vw / 941, vh / 1672) : Math.min(vw / 1672, vh / 941));
  const BOLT = 'M13.5 3 6 13.5h5.5L10.5 21 18 10.5h-5.5Z'; // HUD bolt icon
  let closing = $state(false);
  let shaking = $state<string | null>(null);
  /** Price changed (bet - / +): the prices bump like the HUD values. */
  let bumpKey = $state(0);
  let lastBet = '';
  $effect(() => {
    if (lastBet && bet !== lastBet) bumpKey++;
    lastBet = bet;
  });
  function close() {
    if (closing) return;
    closing = true;
    setTimeout(onclose, 200);
  }
  function pick(c: BuyCard) {
    if (disabled) return;
    if (c.locked) {
      shaking = null;
      requestAnimationFrame(() => (shaking = c.mode));
      return;
    }
    onpick(c);
  }
  function key(e: KeyboardEvent) {
    if (e.key === 'Escape') close();
  }
</script>

<svelte:window bind:innerWidth={vw} bind:innerHeight={vh} onkeydown={key} />

<!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
<div class="buyaki" class:closing class:portrait role="dialog" aria-label={labels.title} tabindex="-1" data-testid="popover-features" style="--k:{k}" onclick={(e) => e.target === e.currentTarget && close()}>
  <div class="cards">
    {#each cards as c, i (c.mode)}
      <button
        class="card"
        class:locked={c.locked}
        class:shake={shaking === c.mode}
        style="--i:{i}"
        data-testid="feature-buy-{c.mode}"
        aria-label="{c.name}, {c.price}"
        aria-disabled={c.locked || disabled}
        onclick={() => pick(c)}
        onanimationend={(e) => e.animationName.endsWith('shake') && (shaking = null)}
      >
        <span class="banner" style="background-image:url({c.banner})"></span>
        <span class="body">
          <span class="vol" aria-label="volatility {c.volatility} / 3">
            {#each [0, 1, 2] as b (b)}<svg viewBox="0 0 24 24" class:on={b < c.volatility} style="--b:{b}"><path d={BOLT} /></svg>{/each}
          </span>
          <span class="name">{c.name}</span>
          {#key bumpKey}<span class="price" class:bump={bumpKey > 0}>{c.price}</span>{/key}
          <span class="go">
            {#if c.locked}<svg viewBox="0 0 24 24" fill="currentColor"><path d="M7 10V8a5 5 0 0 1 10 0v2h1v11H6V10Zm2 0h6V8a3 3 0 0 0-6 0Z" /></svg>{/if}
            {action}
          </span>
        </span>
      </button>
    {/each}
  </div>
  <div class="bar">
    <div class="kv"><span class="l">{labels.balance}</span><span class="v">{balance}</span></div>
    <span class="sep"></span>
    <button class="sq" aria-label={labels.betDown} data-testid="buy-bet-decrease" disabled={betDownDisabled || disabled} onclick={() => onbet(-1)}>
      <svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2.8" stroke-linecap="round"><path d="M6 12h12" /></svg>
    </button>
    <div class="kv bet"><span class="l">{labels.bet}</span><span class="v">{bet}</span></div>
    <button class="sq" aria-label={labels.betUp} data-testid="buy-bet-increase" disabled={betUpDisabled || disabled} onclick={() => onbet(1)}>
      <svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2.8" stroke-linecap="round"><path d="M12 6v12M6 12h12" /></svg>
    </button>
  </div>
  <button class="sq close" aria-label={labels.close} data-testid="buy-close" onclick={close}>
    <svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2.6" stroke-linecap="round"><path d="M6 6l12 12M18 6 6 18" /></svg>
  </button>
</div>

<style>
  .buyaki {
    --glass: rgb(14 10 24 / 0.84);
    --rim: rgb(255 255 255 / 0.16);
    --gold: #ffcf3a;
    position: absolute;
    inset: 0;
    z-index: 45;
    overflow: hidden;
    font-family: Inter, system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif;
    color: #fff;
    user-select: none;
    -webkit-user-select: none;
    backdrop-filter: blur(calc(4px * var(--k))) brightness(0.45) saturate(0.85);
    -webkit-backdrop-filter: blur(calc(4px * var(--k))) brightness(0.45) saturate(0.85);
    animation: dim 0.3s ease-out both;
  }
  .closing {
    animation: undim 0.2s ease-in both;
  }
  @keyframes dim {
    from {
      backdrop-filter: blur(0) brightness(1);
      -webkit-backdrop-filter: blur(0) brightness(1);
    }
  }
  @keyframes undim {
    to {
      backdrop-filter: blur(0) brightness(1);
      -webkit-backdrop-filter: blur(0) brightness(1);
    }
  }
  button {
    font: inherit;
    color: inherit;
    border: 0;
    padding: 0;
    background: none;
    cursor: pointer;
    -webkit-tap-highlight-color: transparent;
  }
  /* design px x --k */
  .cards {
    position: absolute;
    left: 50%;
    top: 47%;
    display: grid;
    grid-auto-flow: column;
    gap: calc(20px * var(--k));
    transform: translate(-50%, -50%);
  }
  .portrait .cards {
    top: 46%;
    grid-auto-flow: row;
    grid-template-columns: repeat(2, auto);
    gap: calc(24px * var(--k));
  }
  .card {
    width: calc(250px * var(--k));
    border-radius: calc(14px * var(--k));
    background: var(--glass);
    box-shadow: 0 calc(10px * var(--k)) calc(26px * var(--k)) rgb(0 0 0 / 0.45);
    overflow: hidden;
    display: block;
    text-align: center;
    transition: transform 0.18s cubic-bezier(0.3, 1.5, 0.5, 1);
    animation: in 0.42s cubic-bezier(0.2, 0.9, 0.3, 1.15) both;
    animation-delay: calc(0.08s + var(--i) * 0.06s);
  }
  .portrait .card {
    width: calc(380px * var(--k));
  }
  @keyframes in {
    from {
      opacity: 0;
      transform: translateY(calc(26px * var(--k))) scale(0.96);
    }
  }
  .card:hover:not(.locked) {
    transform: translateY(calc(-10px * var(--k)));
  }
  .card:active:not(.locked) {
    transform: translateY(calc(-6px * var(--k))) scale(0.98);
  }
  .closing .card {
    animation: out 0.18s ease-in both;
  }
  @keyframes out {
    to {
      opacity: 0;
      transform: translateY(calc(14px * var(--k))) scale(0.97);
    }
  }
  .banner {
    display: block;
    aspect-ratio: 3 / 2;
    background-size: cover;
    background-position: center;
  }
  .body {
    display: grid;
    justify-items: center;
    gap: calc(6px * var(--k));
    padding: calc(12px * var(--k)) calc(14px * var(--k)) calc(14px * var(--k));
  }
  .portrait .body {
    gap: calc(9px * var(--k));
    padding: calc(16px * var(--k)) calc(20px * var(--k)) calc(20px * var(--k));
  }
  .vol {
    display: flex;
  }
  .vol svg {
    width: calc(32px * var(--k));
    height: calc(32px * var(--k));
    margin: calc(-4px * var(--k)) calc(-6px * var(--k));
    overflow: visible;
  }
  .vol path {
    fill: rgb(255 255 255 / 0.16);
  }
  .vol .on path {
    fill: var(--gold);
  }
  .card:hover:not(.locked) .vol .on {
    animation: zap 0.45s ease-out both;
    animation-delay: calc(var(--b) * 0.07s);
  }
  @keyframes zap {
    35% {
      transform: scale(1.25);
    }
  }
  .name {
    font-weight: 800;
    font-size: calc(17px * var(--k));
    letter-spacing: 0.06em;
    text-transform: uppercase;
  }
  .price {
    font-weight: 800;
    font-size: calc(25px * var(--k));
    line-height: 1.1;
    font-variant-numeric: tabular-nums;
  }
  .portrait .name {
    font-size: calc(24px * var(--k));
  }
  .portrait .price {
    font-size: calc(34px * var(--k));
  }
  .price.bump {
    animation: bump 0.25s ease-out;
  }
  @keyframes bump {
    40% {
      transform: scale(1.12);
    }
  }
  .go {
    width: 100%;
    margin-top: calc(4px * var(--k));
    height: calc(44px * var(--k));
    border-radius: calc(7px * var(--k));
    display: flex;
    align-items: center;
    justify-content: center;
    gap: calc(8px * var(--k));
    font-weight: 800;
    font-size: calc(15px * var(--k));
    letter-spacing: 0.12em;
    text-transform: uppercase;
    background: linear-gradient(160deg, #9b74ff, #4d24c4);
    transition: filter 0.15s;
  }
  .portrait .go {
    height: calc(60px * var(--k));
    font-size: calc(20px * var(--k));
  }
  .go svg {
    width: 1.05em;
    height: 1.05em;
  }
  .card:hover:not(.locked) .go {
    filter: brightness(1.2);
  }
  /* not enough balance */
  .locked {
    cursor: not-allowed;
  }
  .locked .banner {
    filter: grayscale(0.9) brightness(0.55);
  }
  .locked .vol,
  .locked .name {
    opacity: 0.55;
  }
  .locked .price {
    color: #ff7a8a;
  }
  .locked .go {
    background: rgb(255 255 255 / 0.08);
    color: rgb(255 255 255 / 0.45);
  }
  .shake {
    animation: shake 0.3s ease-in-out;
  }
  @keyframes shake {
    25% {
      transform: translateX(calc(-5px * var(--k)));
    }
    75% {
      transform: translateX(calc(5px * var(--k)));
    }
  }
  /* square HUD buttons */
  .sq {
    display: grid;
    place-items: center;
    border-radius: 12%;
    background: var(--glass);
    box-shadow:
      inset 0 0 0 1.5px var(--rim),
      0 4px 14px rgb(0 0 0 / 0.35);
    transition:
      filter 0.15s,
      transform 0.08s;
  }
  .sq:hover:not(:disabled) {
    filter: brightness(1.18);
  }
  .sq:active:not(:disabled) {
    transform: scale(0.92);
  }
  .sq:disabled {
    opacity: 0.4;
    cursor: default;
  }
  .sq svg {
    width: 55%;
    height: 55%;
  }
  .close {
    position: absolute;
    right: calc(30px * var(--k));
    top: calc(28px * var(--k));
    width: calc(52px * var(--k));
    height: calc(52px * var(--k));
    animation: fade 0.3s ease-out both;
  }
  @keyframes fade {
    from {
      opacity: 0;
    }
  }
  /* balance / bet bar docked at the bottom of the screen */
  .bar {
    position: absolute;
    left: 50%;
    bottom: 0;
    display: flex;
    align-items: center;
    gap: calc(22px * var(--k));
    height: calc(74px * var(--k));
    padding: 0 calc(16px * var(--k)) 0 calc(26px * var(--k));
    border-radius: calc(14px * var(--k)) calc(14px * var(--k)) 0 0;
    background: var(--glass);
    box-shadow: 0 -4px 14px rgb(0 0 0 / 0.35);
    transform: translateX(-50%);
    animation: rise 0.32s cubic-bezier(0.2, 0.9, 0.3, 1.1) 0.15s both;
  }
  .portrait .bar {
    height: calc(110px * var(--k));
    gap: calc(30px * var(--k));
    padding: 0 calc(24px * var(--k)) 0 calc(36px * var(--k));
  }
  .closing .bar {
    animation: sink 0.2s ease-in both;
  }
  @keyframes rise {
    from {
      transform: translate(-50%, 100%);
    }
  }
  @keyframes sink {
    to {
      transform: translate(-50%, 100%);
    }
  }
  .kv {
    line-height: 1.1;
    white-space: nowrap;
    font-variant-numeric: tabular-nums;
    min-width: calc(150px * var(--k));
    text-align: left;
  }
  .kv .l {
    display: block;
    font-weight: 800;
    font-size: calc(11px * var(--k));
    letter-spacing: 0.08em;
    text-transform: uppercase;
    opacity: 0.7;
    margin-bottom: calc(4px * var(--k));
  }
  .kv .v {
    font-weight: 800;
    font-size: calc(22px * var(--k));
  }
  .portrait .kv .l {
    font-size: calc(16px * var(--k));
  }
  .portrait .kv .v {
    font-size: calc(32px * var(--k));
  }
  .kv.bet {
    min-width: calc(92px * var(--k));
    text-align: center;
  }
  .sep {
    width: 1.5px;
    height: calc(40px * var(--k));
    background: rgb(255 255 255 / 0.14);
  }
  .bar .sq {
    width: calc(46px * var(--k));
    height: calc(46px * var(--k));
  }
  .portrait .bar .sq {
    width: calc(66px * var(--k));
    height: calc(66px * var(--k));
  }
  @media (prefers-reduced-motion: reduce) {
    .buyaki,
    .card,
    .bar,
    .close {
      animation: none !important;
    }
  }
</style>
