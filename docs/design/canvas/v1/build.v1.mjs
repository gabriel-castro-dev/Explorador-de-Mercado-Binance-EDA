// Gera os artboards .dc.html do canvas de design (crypto-forecasting-app)
import { writeFileSync } from 'node:fs';

// ---------- tokens ----------
const T = {
  light: {
    bg: '#fafafa', surface: '#ffffff', muted: '#f4f4f5', accented: '#e4e4e7',
    border: '#e4e4e7', borderMuted: '#ededf0',
    textHi: '#18181b', text: '#27272a', textMuted: '#52525b', textDim: '#8b8b94',
    primary: '#4f46e5', primarySoft: '#eef2ff', onPrimary: '#ffffff',
    warn: '#b45309', warnBg: '#fffbeb', danger: '#b91c1c', dangerBg: '#fef2f2',
    up: '#0f9d58', down: '#d93025', neutral: '#8b8b94',
    sma20: '#2a78d6', sma50: '#eb6834', sma200: '#4a3aa7', ema12: '#eda100', ema26: '#e87ba4',
    bb: '#6b7280', bbFill: 'rgba(107,114,128,.08)', rsi: '#4f46e5',
    upA: 'rgba(15,157,88,.35)', downA: 'rgba(217,48,37,.35)',
    shadow: '0 8px 24px rgba(0,0,0,.10)',
  },
  dark: {
    bg: '#18181b', surface: '#1f1f23', muted: '#26262b', accented: '#2e2e34',
    border: '#2e2e34', borderMuted: '#26262b',
    textHi: '#fafafa', text: '#e4e4e7', textMuted: '#a1a1aa', textDim: '#71717a',
    primary: '#818cf8', primarySoft: 'rgba(129,140,248,.14)', onPrimary: '#18181b',
    warn: '#fbbf24', warnBg: 'rgba(251,191,36,.12)', danger: '#f87171', dangerBg: 'rgba(248,113,113,.12)',
    up: '#26a69a', down: '#ef5350', neutral: '#71717a',
    sma20: '#3987e5', sma50: '#d95926', sma200: '#9085e9', ema12: '#c98500', ema26: '#d55181',
    bb: '#9ca3af', bbFill: 'rgba(156,163,175,.10)', rsi: '#818cf8',
    upA: 'rgba(38,166,154,.35)', downA: 'rgba(239,83,80,.35)',
    shadow: '0 8px 24px rgba(0,0,0,.45)',
  },
};
const FONTS = `<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&amp;family=IBM+Plex+Sans:wght@400;500;600&amp;display=swap">`;
const SANS = `'IBM Plex Sans', system-ui, -apple-system, 'Segoe UI', sans-serif`;
const MONO = `'IBM Plex Mono', ui-monospace, 'SFMono-Regular', Menlo, monospace`;

function baseCss(t) {
  return `
  body { margin:0; background:${t.bg}; color:${t.text}; font-family:${SANS}; font-size:13px; line-height:1.45; -webkit-font-smoothing:antialiased; }
  a { color:${t.primary}; text-decoration:none; } a:hover { color:${t.primary}; text-decoration:underline; }
  * { box-sizing:border-box; }
  .mono { font-family:${MONO}; font-variant-numeric:tabular-nums; }
  .eyebrow { font-family:${MONO}; font-size:11px; font-weight:500; letter-spacing:.06em; text-transform:uppercase; color:${t.textMuted}; }
  .btn { display:inline-flex; align-items:center; justify-content:center; gap:6px; height:32px; padding:0 12px; border-radius:6px; border:1px solid ${t.border}; background:${t.surface}; color:${t.text}; font:500 13px ${SANS}; cursor:pointer; white-space:nowrap; }
  .btn.primary { background:${t.primary}; border-color:${t.primary}; color:${t.onPrimary}; }
  .btn.ghost { border-color:transparent; background:transparent; color:${t.textMuted}; }
  .btn.lg { height:36px; font-size:14px; }
  .btn.block { width:100%; }
  .input { display:flex; align-items:center; gap:8px; height:36px; padding:0 10px; border:1px solid ${t.border}; border-radius:6px; background:${t.surface}; color:${t.text}; font:400 14px ${SANS}; }
  .input .ph { color:${t.textDim}; }
  .label { display:block; font-size:13px; font-weight:500; color:${t.text}; margin-bottom:6px; }
  .hint { font-size:12px; color:${t.textMuted}; }
  .card { background:${t.surface}; border:1px solid ${t.border}; border-radius:8px; }
  .chip { display:inline-flex; align-items:center; gap:6px; height:24px; padding:0 8px; border-radius:999px; border:1px solid ${t.border}; background:${t.surface}; font-size:12px; color:${t.textMuted}; }
  .chip.on { background:${t.primarySoft}; border-color:${t.primary}; color:${t.primary}; }
  .focus { outline:2px solid ${t.primary}; outline-offset:2px; }
  .up { color:${t.up}; } .down { color:${t.down}; }
  .tbl { width:100%; border-collapse:collapse; }
  .tbl th { text-align:right; font-family:${MONO}; font-size:11px; font-weight:500; letter-spacing:.06em; text-transform:uppercase; color:${t.textMuted}; padding:10px 12px; border-bottom:1px solid ${t.border}; white-space:nowrap; }
  .tbl td { text-align:right; padding:10px 12px; border-bottom:1px solid ${t.borderMuted}; font-family:${MONO}; font-variant-numeric:tabular-nums; font-size:13px; color:${t.text}; white-space:nowrap; }
  .tbl th:first-child, .tbl td:first-child { text-align:left; }
  .tbl tr.sel td { background:${t.primarySoft}; }
  .tbl tr.hover td { background:${t.muted}; }
  .sk { background:linear-gradient(90deg, ${t.muted} 25%, ${t.accented} 50%, ${t.muted} 75%); border-radius:4px; }
  `;
}

// ---------- icons (lucide-like, stroke) ----------
const I = (d, s = 16) => `<svg width="${s}" height="${s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${d}</svg>`;
const ic = {
  search: s => I('<circle cx="11" cy="11" r="7"></circle><path d="m20 20-3.5-3.5"></path>', s),
  chevron: s => I('<path d="m6 9 6 6 6-6"></path>', s),
  refresh: s => I('<path d="M21 12a9 9 0 1 1-3-6.7"></path><path d="M21 3v6h-6"></path>', s),
  sun: s => I('<circle cx="12" cy="12" r="4"></circle><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"></path>', s),
  moon: s => I('<path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"></path>', s),
  user: s => I('<circle cx="12" cy="8" r="4"></circle><path d="M4 21a8 8 0 0 1 16 0"></path>', s),
  check: s => I('<path d="m5 12 5 5L20 7"></path>', s),
  alert: s => I('<path d="M12 9v4M12 17h.01"></path><path d="M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z"></path>', s),
  xcircle: s => I('<circle cx="12" cy="12" r="9"></circle><path d="m15 9-6 6M9 9l6 6"></path>', s),
  info: s => I('<circle cx="12" cy="12" r="9"></circle><path d="M12 16v-4M12 8h.01"></path>', s),
  eye: s => I('<path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12z"></path><circle cx="12" cy="12" r="3"></circle>', s),
  back: s => I('<path d="m12 19-7-7 7-7M19 12H5"></path>', s),
  mail: s => I('<rect x="3" y="5" width="18" height="14" rx="2"></rect><path d="m3 7 9 6 9-6"></path>', s),
  clock: s => I('<circle cx="12" cy="12" r="9"></circle><path d="M12 7v5l3 2"></path>', s),
  layers: s => I('<path d="m12 2 9 5-9 5-9-5 9-5z"></path><path d="m3 12 9 5 9-5M3 17l9 5 9-5"></path>', s),
  table: s => I('<rect x="3" y="4" width="18" height="16" rx="2"></rect><path d="M3 10h18M9 4v16"></path>', s),
  trend: s => I('<path d="m3 17 6-6 4 4 8-8"></path><path d="M14 7h7v7"></path>', s),
  menu: s => I('<path d="M4 6h16M4 12h16M4 18h16"></path>', s),
  x: s => I('<path d="M18 6 6 18M6 6l12 12"></path>', s),
  sliders: s => I('<path d="M4 21v-7M4 10V3M12 21v-9M12 8V3M20 21v-5M20 12V3M1 14h6M9 8h6M17 16h6"></path>', s),
  logout: s => I('<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9"></path>', s),
  sort: s => I('<path d="m7 15 5 5 5-5M7 9l5-5 5 5"></path>', s),
  sortDown: s => I('<path d="m6 9 6 6 6-6"></path>', s),
  dot: s => I('<circle cx="12" cy="12" r="5" fill="currentColor" stroke="none"></circle>', s),
  lock: s => I('<rect x="4" y="11" width="16" height="10" rx="2"></rect><path d="M8 11V7a4 4 0 0 1 8 0v4"></path>', s),
  external: s => I('<path d="M14 4h6v6M20 4l-9 9M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5"></path>', s),
  inbox: s => I('<path d="M22 12h-6l-2 3h-4l-2-3H2"></path><path d="M5.5 5.1 2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.5-6.9A2 2 0 0 0 16.8 4H7.2a2 2 0 0 0-1.7 1.1z"></path>', s),
  sparkle: s => I('<path d="M12 3v4M12 17v4M3 12h4M17 12h4M5.6 5.6l2.8 2.8M15.6 15.6l2.8 2.8M5.6 18.4l2.8-2.8M15.6 8.4l2.8-2.8"></path>', s),
};

// ---------- data ----------
function rng(seed) { let s = seed >>> 0; return () => { s = (s * 1664525 + 1013904223) >>> 0; return s / 4294967296; }; }
function genCandles(n, seed = 7, base = 113000) {
  const r = rng(seed); const out = []; let c = base;
  for (let i = 0; i < n; i++) {
    const drift = Math.sin(i / 11) * 180 + (r() - 0.48) * 900;
    const o = c; c = Math.max(base * 0.8, o + drift);
    const hi = Math.max(o, c) + r() * 500; const lo = Math.min(o, c) - r() * 500;
    const vol = 600 + r() * 1400 + (Math.abs(drift) > 400 ? 900 : 0);
    out.push({ o, h: hi, l: lo, c, v: vol });
  }
  return out;
}
const sma = (arr, p) => arr.map((_, i) => i + 1 < p ? null : arr.slice(i + 1 - p, i + 1).reduce((a, b) => a + b, 0) / p);
function ema(arr, p) { const k = 2 / (p + 1); let e = null; return arr.map((v, i) => { if (i + 1 < p) return null; if (e === null) { e = arr.slice(0, p).reduce((a, b) => a + b, 0) / p; return e; } e = v * k + e * (1 - k); return e; }); }
function rsi(arr, p = 14) { return arr.map((_, i) => { if (i < p) return null; let g = 0, l = 0; for (let j = i - p + 1; j <= i; j++) { const d = arr[j] - arr[j - 1]; if (d > 0) g += d; else l -= d; } if (l === 0) return 100; const rs = (g / p) / (l / p); return 100 - 100 / (1 + rs); }); }

// ---------- chart svg ----------
function chartSvg(t, W, H, o = {}) {
  const { total = 130, show = 92, crossAt = 0.62, cut = true, forecast = true, panes = ['rsi', 'macd'], overlays = ['sma20', 'sma50'], skeleton = false, empty = false, mobile = false, seed = 7, padTop = mobile ? 78 : 52 } = o;
  const data = genCandles(total, seed); const closes = data.map(d => d.c);
  const S = { sma20: sma(closes, 20), sma50: sma(closes, 50), sma200: sma(closes, 200), ema12: ema(closes, 12), ema26: ema(closes, 26) };
  const bbm = sma(closes, 20); const bbu = bbm.map((m, i) => m == null ? null : m + 900), bbl = bbm.map((m, i) => m == null ? null : m - 900);
  const R = rsi(closes); const mac = closes.map((_, i) => S.ema12[i] == null || S.ema26[i] == null ? null : S.ema12[i] - S.ema26[i]);
  const macSig = ema(mac.map(v => v ?? 0), 9).map((v, i) => mac[i] == null || i < 34 ? null : v);
  const first = total - show; const vis = data.slice(first);
  const axW = mobile ? 62 : 64; const padL = 8; const fcW = forecast ? Math.round((W - axW) * 0.11) : 0;
  const plotW = W - axW - padL - fcW; const step = plotW / show; const cw = Math.max(2, Math.floor(step * 0.62));
  const x = i => padL + i * step + step / 2;
  const priceH = panes.length ? Math.round(H * (panes.length === 2 ? 0.56 : 0.72)) : H;
  const paneH = panes.length ? Math.round((H - priceH) / panes.length) : 0;
  const hi = Math.max(...vis.map(d => d.h)) * 1.004, lo = Math.min(...vis.map(d => d.l)) * 0.996;
  const py = v => padTop + (priceH - padTop - priceH * 0.22) * (1 - (v - lo) / (hi - lo));
  const volMax = Math.max(...vis.map(d => d.v)); const volBase = priceH - 4; const volH = priceH * 0.18;
  let s = `<svg width="${W}" height="${H}" viewBox="0 0 ${W} ${H}" font-family="${MONO}" font-size="11" style="display:block">`;
  // grid + axis price
  const ticks = 5; for (let k = 0; k <= ticks; k++) { const v = lo + (hi - lo) * k / ticks; const y = py(v); s += `<line x1="0" x2="${W - axW}" y1="${y.toFixed(1)}" y2="${y.toFixed(1)}" stroke="${t.borderMuted}"></line><text x="${W - axW + 8}" y="${(y + 4).toFixed(1)}" fill="${t.textDim}">${Math.round(v).toLocaleString('pt-BR')}</text>`; }
  if (skeleton) { s += `<rect x="${padL}" y="${padTop - 12}" width="${plotW}" height="${priceH - padTop - 8}" rx="4" fill="${t.muted}"></rect>`; panes.forEach((p, pi) => { const top = priceH + pi * paneH; s += `<rect x="${padL}" y="${top + 14}" width="${plotW}" height="${paneH - 28}" rx="4" fill="${t.muted}"></rect>`; }); return s + '</svg>'; }
  if (empty) { return s + `</svg>`; }
  // pane separators
  panes.forEach((p, pi) => { const top = priceH + pi * paneH; s += `<line x1="0" x2="${W}" y1="${top}" y2="${top}" stroke="${t.border}"></line>`; });
  // BB band
  if (overlays.includes('bb')) { let up = '', lowp = ''; vis.forEach((d, i) => { const gi = first + i; if (bbu[gi] == null) return; up += `${up ? 'L' : 'M'}${x(i).toFixed(1)},${py(bbu[gi]).toFixed(1)} `; }); const pts = []; vis.forEach((d, i) => { const gi = first + i; if (bbl[gi] != null) pts.push([x(i), py(bbl[gi])]); }); lowp = pts.reverse().map(p => `L${p[0].toFixed(1)},${p[1].toFixed(1)}`).join(' '); if (up) s += `<path d="${up}${lowp}Z" fill="${t.bbFill}"></path><path d="${up}" fill="none" stroke="${t.bb}" stroke-dasharray="2 3"></path><path d="${'M' + pts.reverse().map(p => `${p[0].toFixed(1)},${p[1].toFixed(1)}`).join(' L')}" fill="none" stroke="${t.bb}" stroke-dasharray="2 3"></path>`; }
  // volume
  vis.forEach((d, i) => { const h = volH * d.v / volMax; s += `<rect x="${(x(i) - cw / 2).toFixed(1)}" y="${(volBase - h).toFixed(1)}" width="${cw}" height="${h.toFixed(1)}" fill="${d.c >= d.o ? t.upA : t.downA}"></rect>`; });
  // candles
  vis.forEach((d, i) => { const upc = d.c >= d.o; const col = upc ? t.up : t.down; const y1 = py(Math.max(d.o, d.c)), y2 = py(Math.min(d.o, d.c)); s += `<line x1="${x(i).toFixed(1)}" x2="${x(i).toFixed(1)}" y1="${py(d.h).toFixed(1)}" y2="${py(d.l).toFixed(1)}" stroke="${col}"></line><rect x="${(x(i) - cw / 2).toFixed(1)}" y="${y1.toFixed(1)}" width="${cw}" height="${Math.max(1, y2 - y1).toFixed(1)}" fill="${col}"></rect>`; });
  // overlays lines
  const styleOf = { sma20: [t.sma20, 1, ''], sma50: [t.sma50, 1.5, ''], sma200: [t.sma200, 2, ''], ema12: [t.ema12, 1, '4 3'], ema26: [t.ema26, 1.5, '4 3'] };
  overlays.filter(k => styleOf[k]).forEach(k => { let d = '', pen = false; vis.forEach((_, i) => { const v = S[k][first + i]; if (v == null) { pen = false; return; } d += `${pen ? 'L' : 'M'}${x(i).toFixed(1)},${py(v).toFixed(1)} `; pen = true; }); const [c, w, da] = styleOf[k]; s += `<path d="${d}" fill="none" stroke="${c}" stroke-width="${w}" ${da ? `stroke-dasharray="${da}"` : ''}></path>`; });
  // panes
  panes.forEach((p, pi) => {
    const top = priceH + pi * paneH; const ph = paneH;
    if (p === 'rsi') {
      const ry = v => top + 14 + (ph - 28) * (1 - v / 100);
      s += `<rect x="0" y="${ry(70).toFixed(1)}" width="${W - axW}" height="${(ry(30) - ry(70)).toFixed(1)}" fill="${t.primary}" opacity="0.05"></rect>`;
      [30, 70].forEach(v => s += `<line x1="0" x2="${W - axW}" y1="${ry(v).toFixed(1)}" y2="${ry(v).toFixed(1)}" stroke="${t.border}" stroke-dasharray="3 3"></line><text x="${W - axW + 8}" y="${(ry(v) + 4).toFixed(1)}" fill="${t.textDim}">${v}</text>`);
      let d = '', pen = false; vis.forEach((_, i) => { const v = R[first + i]; if (v == null) { pen = false; return; } d += `${pen ? 'L' : 'M'}${x(i).toFixed(1)},${ry(v).toFixed(1)} `; pen = true; }); s += `<path d="${d}" fill="none" stroke="${t.rsi}" stroke-width="1.5"></path>`;
      s += `<text x="${padL + 2}" y="${top + 16}" fill="${t.textMuted}" font-size="11">RSI 14 <tspan fill="${t.rsi}">${R[total - 1].toFixed(1).replace('.', ',')}</tspan></text>`;
    } else if (p === 'macd') {
      const vals = vis.map((_, i) => mac[first + i]).filter(v => v != null); const mx = Math.max(...vals.map(Math.abs)) * 1.1;
      const my = v => top + 14 + (ph - 28) * (1 - (v + mx) / (2 * mx));
      s += `<line x1="0" x2="${W - axW}" y1="${my(0).toFixed(1)}" y2="${my(0).toFixed(1)}" stroke="${t.border}"></line>`;
      vis.forEach((_, i) => { const gi = first + i; if (mac[gi] == null || macSig[gi] == null) return; const h = mac[gi] - macSig[gi]; const y0 = my(0), y1 = my(h); s += `<rect x="${(x(i) - cw / 2).toFixed(1)}" y="${Math.min(y0, y1).toFixed(1)}" width="${cw}" height="${Math.max(1, Math.abs(y1 - y0)).toFixed(1)}" fill="${h >= 0 ? t.up : t.down}" opacity="0.6"></rect>`; });
      [[mac, t.sma20, 1.5], [macSig, t.sma50, 1.5]].forEach(([arr, c, w]) => { let d = '', pen = false; vis.forEach((_, i) => { const v = arr[first + i]; if (v == null) { pen = false; return; } d += `${pen ? 'L' : 'M'}${x(i).toFixed(1)},${my(v).toFixed(1)} `; pen = true; }); s += `<path d="${d}" fill="none" stroke="${c}" stroke-width="${w}"></path>`; });
      s += `<text x="${padL + 2}" y="${top + 16}" fill="${t.textMuted}" font-size="11">MACD 12·26·9 <tspan fill="${t.sma20}">${mac[total - 1].toFixed(0).replace('-', '−')}</tspan> <tspan fill="${t.sma50}">${macSig[total - 1].toFixed(0).replace('-', '−')}</tspan></text>`;
    }
  });
  // time axis
  const labels = mobile ? 4 : 7; for (let k = 0; k < labels; k++) { const i = Math.round(k * (show - 1) / (labels - 1)); const abs = i + 6; const day = 15 + Math.floor(abs / 24); const hr = abs % 24; const anchor = k === 0 ? 'start' : k === labels - 1 ? 'end' : 'middle'; const xx = k === 0 ? padL : k === labels - 1 ? x(i) : x(i); s += `<text x="${xx.toFixed(1)}" y="${H - 6}" fill="${t.textDim}" text-anchor="${anchor}">${hr < 4 || k === 0 ? `${day} ago` : `${String(hr).padStart(2, '0')}:00`}</text>`; }
  // crosshair
  if (crossAt) { const ci = Math.round(show * crossAt); const cx = x(ci); s += `<line x1="${cx.toFixed(1)}" x2="${cx.toFixed(1)}" y1="0" y2="${H - 18}" stroke="${t.textDim}" stroke-dasharray="3 3"></line>`; const d = vis[ci]; const cy = py(d.c); s += `<line x1="0" x2="${W - axW}" y1="${cy.toFixed(1)}" y2="${cy.toFixed(1)}" stroke="${t.textDim}" stroke-dasharray="3 3"></line><rect x="${W - axW + 2}" y="${(cy - 9).toFixed(1)}" width="${axW - 4}" height="18" rx="3" fill="${t.textHi}"></rect><text x="${W - axW + 8}" y="${(cy + 4).toFixed(1)}" fill="${t.bg}">${Math.round(d.c).toLocaleString('pt-BR')}</text><rect x="${(cx - 42).toFixed(1)}" y="${H - 19}" width="84" height="17" rx="3" fill="${t.textHi}"></rect><text x="${cx.toFixed(1)}" y="${H - 7}" fill="${t.bg}" text-anchor="middle">18 ago 14:00</text>`; }
  // cut line + forecast slot
  if (cut) { const cx = x(show - 1) + step / 2 + 2; s += `<line x1="${cx.toFixed(1)}" x2="${cx.toFixed(1)}" y1="0" y2="${H - 18}" stroke="${t.primary}" stroke-dasharray="2 3" opacity="0.9"></line>`;
    if (forecast) { s += `<defs><pattern id="hatch${seed}" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="6" stroke="${t.primary}" stroke-width="1" opacity="0.18"></line></pattern></defs><rect x="${cx + 1}" y="0" width="${W - axW - cx - 1}" height="${priceH}" fill="url(#hatch${seed})"></rect>`; const lc = vis[show - 1].c; const y0 = py(lc); s += `<path d="M${cx},${y0.toFixed(1)} L${(W - axW - 4).toFixed(1)},${(y0 - 40).toFixed(1)} L${(W - axW - 4).toFixed(1)},${(y0 + 44).toFixed(1)} Z" fill="${t.primary}" opacity="0.10"></path><path d="M${cx},${y0.toFixed(1)} L${(W - axW - 4).toFixed(1)},${(y0 + 2).toFixed(1)}" stroke="${t.primary}" stroke-dasharray="3 3" opacity="0.6"></path>`; if (!mobile) s += `<text x="${cx + 8}" y="${(priceH - 10).toFixed(1)}" fill="${t.primary}" font-size="11" opacity="0.9">previsão · em breve</text>`; }
  }
  return s + '</svg>';
}

// ---------- shared blocks ----------
function legend(t, o = {}) {
  const { symbol = 'BTCUSDT', tf = '1h', warm = true, rows = [['SMA 20', t.sma20, '113.512,3', ''], ['SMA 50', t.sma50, '112.980,7', '']], mobile = false } = o;
  const ohlc = `<span style="color:${t.textMuted}">A</span> <span class="mono">113.250,1</span> <span style="color:${t.textMuted}">M</span> <span class="mono">113.900,0</span> <span style="color:${t.textMuted}">m</span> <span class="mono">112.800,5</span> <span style="color:${t.textMuted}">F</span> <span class="mono" style="color:${t.up}">113.512,3</span> <span style="color:${t.textMuted}">Vol</span> <span class="mono">1.284,5</span>`;
  return `<div style="position:absolute; left:12px; top:10px; display:flex; flex-direction:column; gap:4px; font-size:12px; pointer-events:none;">
    <div style="display:flex; align-items:center; gap:8px; flex-wrap:wrap;"><span style="font-weight:600; color:${t.textHi}">${symbol}</span><span class="mono" style="color:${t.textMuted}">· ${tf} · <span style="color:${t.textDim}">18 ago 14:00 UTC</span></span>${mobile ? '' : `<span>${ohlc}</span>`}</div>
    ${mobile ? `<div style="font-size:11px">${ohlc}</div>` : ''}
    <div style="display:flex; gap:12px; flex-wrap:wrap; font-size:12px">${rows.map(([n, c, v, note]) => `<span style="display:inline-flex; align-items:center; gap:6px"><span style="width:12px; height:2px; background:${c}; display:inline-block"></span><span style="color:${t.textMuted}">${n}</span><span class="mono" style="color:${t.text}">${v}</span>${note ? `<span style="color:${t.textDim}; font-size:11px">${note}</span>` : ''}</span>`).join('')}</div>
  </div>`;
}

function stamp(t, o = {}) {
  const { state = 'fresh', mobile = false } = o; // fresh | stale | loading
  const col = state === 'stale' ? t.warn : t.textMuted; const dot = state === 'stale' ? t.warn : t.up; const bg = state === 'stale' ? t.warnBg : t.surface;
  const txt = state === 'stale' ? (mobile ? 'Velas: há 31 h' : 'Velas atualizadas em 18 ago 00:00 UTC · há 31 h') : (mobile ? 'Velas: 19 ago 00:00 UTC · há 6 h' : 'Velas: 19 ago 00:00 UTC · há 6 h');
  return `<span class="mono" title="Candles e indicadores atualizam 1x/dia (~00:05 UTC); resumo 24h de hora em hora. Nada é tempo real." style="display:inline-flex; align-items:center; gap:8px; height:32px; padding:0 10px; border:1px solid ${state === 'stale' ? t.warn : t.border}; border-radius:6px; background:${bg}; color:${col}; font-size:11px; letter-spacing:.02em; white-space:nowrap;">${state === 'stale' ? `<span style="color:${t.warn}; display:inline-flex">${ic.alert(14)}</span>` : `<span style="width:7px; height:7px; border-radius:999px; background:${dot}; display:inline-block"></span>`}<span style="font-weight:500; text-transform:uppercase; letter-spacing:.06em">snapshot</span><span style="color:${t.border}">|</span><span>${txt}</span></span>`;
}

function header(t, o = {}) {
  const { active = 'dash', mode = 'light', mobile = false, w } = o;
  const nav = [['dash', 'Dashboard', ic.trend(16)], ['mercado', 'Mercado', ic.table(16)], ['prev', 'Previsões', ic.sparkle(16)]];
  const navHtml = nav.map(([k, l, i]) => `<a href="#" aria-current="${k === active ? 'page' : 'false'}" ${k === 'prev' ? 'aria-disabled="true"' : ''} style="display:inline-flex; align-items:center; gap:6px; height:32px; padding:0 10px; border-radius:6px; font-weight:500; color:${k === active ? t.textHi : t.textMuted}; background:${k === active ? t.muted : 'transparent'}; text-decoration:none; ${k === 'prev' ? 'opacity:.75' : ''}">${i}<span>${l}</span>${k === 'prev' ? `<span class="mono" style="font-size:10px; padding:1px 6px; border-radius:999px; border:1px solid ${t.border}; color:${t.textDim}; letter-spacing:.04em">EM BREVE</span>` : ''}</a>`).join('');
  if (mobile) return `<header style="display:flex; align-items:center; justify-content:space-between; height:52px; padding:0 14px; background:${t.surface}; border-bottom:1px solid ${t.border};">
    <div style="display:flex; align-items:center; gap:8px"><span style="width:24px; height:24px; border-radius:6px; background:${t.textHi}; color:${t.bg}; display:inline-flex; align-items:center; justify-content:center; font:600 12px ${MONO}">cf</span><span style="font-weight:600; color:${t.textHi}">crypto forecasting</span></div>
    <div style="display:flex; gap:4px"><button class="btn ghost" aria-label="Alternar tema" style="width:36px; padding:0">${mode === 'light' ? ic.moon(18) : ic.sun(18)}</button><button class="btn ghost" aria-label="Conta" style="width:36px; padding:0">${ic.user(18)}</button></div>
  </header>`;
  return `<header style="display:flex; align-items:center; justify-content:space-between; height:56px; padding:0 24px; background:${t.surface}; border-bottom:1px solid ${t.border};">
    <div style="display:flex; align-items:center; gap:28px">
      <div style="display:flex; align-items:center; gap:10px"><span style="width:28px; height:28px; border-radius:6px; background:${t.textHi}; color:${t.bg}; display:inline-flex; align-items:center; justify-content:center; font:600 13px ${MONO}">cf</span><span style="font-weight:600; color:${t.textHi}; letter-spacing:-.01em">crypto forecasting</span></div>
      <nav style="display:flex; gap:4px" aria-label="Principal">${navHtml}</nav>
    </div>
    <div style="display:flex; align-items:center; gap:6px">
      <button class="btn ghost" aria-label="Alternar tema claro/escuro">${mode === 'light' ? ic.moon(16) : ic.sun(16)}</button>
      <button class="btn ghost" style="gap:8px"><span style="width:24px; height:24px; border-radius:999px; background:${t.primarySoft}; color:${t.primary}; display:inline-flex; align-items:center; justify-content:center; font:600 11px ${SANS}">GC</span><span>gabriel@…</span>${ic.chevron(14)}</button>
    </div>
  </header>`;
}

function toolbar(t, o = {}) {
  const { tf = '1h', state = 'fresh', symbol = 'BTCUSDT', open = false } = o;
  const tfs = ['15m', '1h', '1d'].map(k => `<button class="btn" aria-pressed="${k === tf}" style="height:30px; border:none; border-radius:4px; padding:0 12px; background:${k === tf ? t.surface : 'transparent'}; color:${k === tf ? t.textHi : t.textMuted}; box-shadow:${k === tf ? '0 1px 2px rgba(0,0,0,.08)' : 'none'}; font-family:${MONO}">${k}</button>`).join('');
  return `<div style="display:flex; align-items:center; justify-content:space-between; gap:12px; padding:12px 24px; flex-wrap:wrap">
    <div style="display:flex; align-items:center; gap:10px; position:relative">
      <button class="btn" aria-haspopup="listbox" style="min-width:220px; justify-content:space-between; padding-left:10px"><span style="display:inline-flex; gap:8px; align-items:center"><span style="color:${t.textDim}">${ic.search(14)}</span><span class="mono" translate="no" style="font-weight:500; color:${t.textHi}">${symbol}</span><span style="color:${t.textMuted}; font-weight:400">Bitcoin / Tether</span></span>${ic.chevron(14)}</button>
      <div role="radiogroup" aria-label="Timeframe" style="display:inline-flex; gap:2px; padding:2px; background:${t.muted}; border:1px solid ${t.border}; border-radius:6px">${tfs}</div>
      <span class="hint mono" style="color:${t.textDim}">1h · últimos 30 dias</span>
      ${open ? symbolMenu(t) : ''}
    </div>
    <div style="display:flex; align-items:center; gap:8px">${stamp(t, { state })}<button class="btn" aria-label="Atualizar dados">${ic.refresh(14)}<span>Atualizar</span></button></div>
  </div>`;
}
function symbolMenu(t) {
  const rows = [['BTCUSDT', 'Bitcoin', '113.512,3', '+1,84'], ['ETHUSDT', 'Ethereum', '4.312,9', '−0,62'], ['SOLUSDT', 'Solana', '186,40', '+3,11'], ['BNBUSDT', 'BNB', '842,1', '+0,20'], ['XRPUSDT', 'XRP', '3,012', '−1,05'], ['DOGEUSDT', 'Dogecoin', '0,2310', '+0,00']];
  return `<div class="card" role="listbox" style="position:absolute; top:40px; left:0; width:340px; box-shadow:${t.shadow}; z-index:5; overflow:hidden">
    <div class="input" style="border:none; border-bottom:1px solid ${t.border}; border-radius:0; height:40px"><span style="color:${t.textDim}">${ic.search(14)}</span><span>so</span><span style="width:1px; height:16px; background:${t.primary}"></span></div>
    ${rows.map(([s, n, p, v], i) => `<div role="option" aria-selected="${i === 0}" style="display:flex; align-items:center; justify-content:space-between; padding:8px 12px; background:${i === 2 ? t.muted : 'transparent'}"><span style="display:flex; flex-direction:column"><span class="mono" style="font-weight:500; color:${t.textHi}">${s}</span><span class="hint">${n}</span></span><span style="display:flex; flex-direction:column; align-items:flex-end"><span class="mono">${p}</span><span class="mono" style="font-size:11px; color:${v.startsWith('+') ? t.up : v.startsWith('−') ? t.down : t.textMuted}">${v.startsWith('+') && v !== '+0,00' ? '▲ ' : v.startsWith('−') ? '▼ ' : ''}${v} %</span></span></div>`).join('')}
    <div class="hint" style="padding:8px 12px; border-top:1px solid ${t.border}; display:flex; justify-content:space-between"><span>20 ativos · top 20 por volume 24h</span><span class="mono">↑↓ · Enter</span></div>
  </div>`;
}

function togglesPanel(t, o = {}) {
  const { on = ['sma20', 'sma50', 'vol', 'rsi', 'macd'], w = 264, hint = false } = o;
  const groups = [
    ['Sobre o preço', [['sma20', 'SMA 20', t.sma20, 'solid'], ['sma50', 'SMA 50', t.sma50, 'solid'], ['sma200', 'SMA 200', t.sma200, 'solid'], ['ema12', 'EMA 12', t.ema12, 'dash'], ['ema26', 'EMA 26', t.ema26, 'dash'], ['bb', 'Bollinger 20·2', t.bb, 'dot'], ['vol', 'Volume', t.textDim, 'bar']]],
    ['Painéis abaixo', [['rsi', 'RSI 14', t.rsi, 'solid'], ['macd', 'MACD 12·26·9', t.sma20, 'solid']]],
  ];
  const sw = (c, st) => st === 'bar' ? `<span style="display:inline-flex; gap:1px; align-items:flex-end; height:10px"><i style="width:3px; height:6px; background:${c}; display:block"></i><i style="width:3px; height:10px; background:${c}; display:block"></i><i style="width:3px; height:4px; background:${c}; display:block"></i></span>` : `<span style="width:16px; height:0; border-top:2px ${st === 'solid' ? 'solid' : st === 'dash' ? 'dashed' : 'dotted'} ${c}; display:inline-block"></span>`;
  return `<aside class="card" aria-label="Indicadores" style="width:${w}px; flex:none; display:flex; flex-direction:column; overflow:hidden">
    <div style="display:flex; align-items:center; justify-content:space-between; padding:10px 12px 8px; border-bottom:1px solid ${t.border}"><span style="font-weight:600; color:${t.textHi}">Indicadores</span><span class="hint">persistem no navegador</span></div>
    ${groups.map(([g, items]) => `<div style="padding:8px 6px 4px"><div class="eyebrow" style="padding:4px 6px 6px">${g}</div>${items.map(([k, l, c, st]) => { const isOn = on.includes(k); return `<label style="display:flex; align-items:center; gap:10px; height:32px; padding:0 6px; border-radius:6px; cursor:pointer; ${k === 'sma50' && hint ? `outline:2px solid ${t.primary}; outline-offset:-2px;` : ''}"><span role="checkbox" tabindex="0" aria-checked="${isOn}" style="width:16px; height:16px; border-radius:4px; border:1px solid ${isOn ? t.primary : t.border}; background:${isOn ? t.primary : t.surface}; color:${t.onPrimary}; display:inline-flex; align-items:center; justify-content:center">${isOn ? ic.check(12) : ''}</span>${sw(c, st)}<span style="flex:1; color:${isOn ? t.text : t.textMuted}">${l}</span>${k === 'sma200' ? `<span class="hint mono" title="Warm-up: SMA 200 só existe a partir da 200ª vela" style="font-size:10px">warm-up</span>` : ''}</label>`; }).join('')}</div>`).join('')}
    <div style="margin-top:auto; padding:10px 12px; border-top:1px solid ${t.border}; display:flex; flex-direction:column; gap:8px">
      <div class="hint" style="display:flex; gap:6px; align-items:flex-start"><span style="color:${t.textDim}; flex:none; margin-top:1px">${ic.info(14)}</span><span>Linhas começam só depois da janela de cálculo (warm-up). Não é erro.</span></div>
      <div style="display:flex; gap:6px"><button class="btn ghost" style="height:28px; font-size:12px; padding:0 8px">Restaurar padrão</button><button class="btn ghost" style="height:28px; font-size:12px; padding:0 8px">Limpar tudo</button></div>
    </div>
  </aside>`;
}

function kpiStrip(t, o = {}) {
  const { mobile = false, nulls = false } = o;
  const items = [['Último preço', '113.512,3', 'USDT'], ['Variação 24h', nulls ? '—' : '▲ +2.048,9 · +1,84 %', '', nulls ? '' : 'up'], ['Abertura', '111.463,4', 'USDT'], ['Máx / Mín', nulls ? '— / —' : '114.120,0 · 110.902,1', ''], ['Preço médio pond.', '112.877,4', 'USDT'], ['Bid / Ask', nulls ? '— / —' : '113.510,0 / 113.512,9', 'spread 0,003 %'], ['Volume 24h', '38.412 BTC', '4,33 bi USDT · 4,21 mi trades']];
  return `<section aria-label="Resumo 24h" class="card" style="display:flex; flex-direction:column">
    <div style="display:flex; align-items:center; justify-content:space-between; padding:8px 14px 6px; border-bottom:1px solid ${t.borderMuted}"><span class="eyebrow">Resumo 24h · BTCUSDT</span><span class="hint mono" style="font-size:11px">${mobile ? '14:00 UTC · há 12 min' : 'snapshot 19 ago 14:00 UTC · há 12 min · atualiza de hora em hora'}</span></div>
    <div style="display:${mobile ? 'grid' : 'flex'}; ${mobile ? 'grid-template-columns:repeat(2, minmax(0,1fr));' : ''}">
    ${items.map(([l, v, s, cls], i) => `<div style="display:flex; flex-direction:column; gap:2px; padding:10px ${mobile ? 12 : 14}px; ${mobile ? 'min-width:0;' : 'flex:1;'} ${i < items.length - 1 && !mobile ? `border-right:1px solid ${t.borderMuted}` : ''} ${mobile && i % 2 === 0 ? `border-right:1px solid ${t.borderMuted}` : ''} ${mobile && i < items.length - 2 ? `border-bottom:1px solid ${t.borderMuted}` : ''}"><span class="hint" style="font-size:11px; white-space:nowrap">${l}</span><span class="mono ${cls || ''}" style="font-size:${mobile ? 12.5 : 14}px; font-weight:500; white-space:nowrap; color:${cls ? '' : t.textHi}">${v}</span>${s ? `<span class="hint mono" style="font-size:11px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis">${s}</span>` : ''}</div>`).join('')}
    </div>
  </section>`;
}

function wrap(t, title, body, { w, h, mode }) {
  return `<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <script src="./support.js"></script>
</head>
<body>
<x-dc>
<helmet>
  ${FONTS}
  <style>${baseCss(t)}</style>
</helmet>
<div data-mode="${mode}" aria-label="${title}" style="width:${w}px; height:${h}px; background:${t.bg}; color:${t.text}; font-family:${SANS}; overflow:hidden; display:flex; flex-direction:column; position:relative;">
${body}
</div>
</x-dc>
<script data-dc-script data-props='{"$preview":{"width":${w},"height":${h}}}'>
class Component extends DCLogic {
  renderVals() { return {}; }
}
</script>
</body>
</html>`;
}

// ---------- screens ----------
function dashboard(mode, o = {}) {
  const t = T[mode]; const W = 1440, H = 960;
  const { state = 'fresh', open = false, onboarding = false, overlays = ['sma20', 'sma50'], on = ['sma20', 'sma50', 'vol', 'rsi', 'macd'], title = 'Dashboard' } = o;
  const chartW = W - 48 - 264 - 16; const chartH = 652;
  const body = `
  ${header(t, { active: 'dash', mode })}
  <h1 style="position:absolute; width:1px; height:1px; overflow:hidden; clip:rect(0 0 0 0); margin:-1px">Dashboard</h1>
  ${toolbar(t, { state, open })}
  <main style="display:flex; gap:16px; padding:0 24px 16px; flex:1; min-height:0">
    <section class="card" aria-label="Gráfico" style="flex:1; position:relative; overflow:hidden; display:flex; flex-direction:column">
      <div style="position:relative; height:${chartH}px; background:${t.surface}">
        ${chartSvg(t, chartW, chartH, { overlays, panes: on.filter(k => k === 'rsi' || k === 'macd'), cut: true, forecast: true })}
        ${legend(t, { rows: [['SMA 20', t.sma20, '113.512,3', ''], ['SMA 50', t.sma50, '112.980,7', 'warm-up até 16 ago']] })}
        ${onboarding ? `<div class="card" role="dialog" aria-label="Dica" style="position:absolute; right:16px; top:48px; width:300px; padding:14px 16px; box-shadow:${t.shadow}; border-color:${t.primary}"><div style="display:flex; justify-content:space-between; align-items:flex-start; gap:8px"><span style="font-weight:600; color:${t.textHi}">Seu primeiro snapshot</span><button class="btn ghost" aria-label="Fechar" style="height:24px; width:24px; padding:0">${ic.x(14)}</button></div><p style="margin:6px 0 10px; color:${t.textMuted}">Abrimos o <span class="mono" style="color:${t.text}">BTCUSDT</span> em 1h. Escolha outro ativo no seletor ou ligue indicadores no painel ao lado — suas escolhas ficam salvas neste navegador.</p><div style="display:flex; gap:8px; justify-content:flex-end"><button class="btn ghost" style="height:28px">Não mostrar de novo</button><button class="btn primary" style="height:28px">Entendi</button></div></div>` : ''}
      </div>
      <div style="display:flex; align-items:center; justify-content:space-between; padding:8px 12px; border-top:1px solid ${t.border}; font-size:11px; color:${t.textDim}" class="mono"><span>Eixo em UTC · arraste para navegar · scroll para zoom · <span style="color:${t.primary}">┆</span> linha de corte = último dado observado</span><span>exibindo 92 de 720 velas · retenção 30 dias</span></div>
    </section>
    ${togglesPanel(t, { on, hint: onboarding })}
  </main>
  <div style="padding:0 24px 24px">${kpiStrip(t)}</div>`;
  return wrap(t, title, body, { w: W, h: H, mode });
}

function dashboardMobile(mode) {
  const t = T[mode]; const W = 390, H = 844;
  const body = `
  ${header(t, { mobile: true, mode })}
  <div style="display:flex; flex-direction:column; gap:8px; padding:10px 12px 0">
    <div style="display:flex; gap:8px"><button class="btn" style="flex:1; height:40px; justify-content:space-between"><span style="display:inline-flex; gap:8px; align-items:center">${ic.search(14)}<span class="mono" style="font-weight:500; color:${t.textHi}">BTCUSDT</span></span>${ic.chevron(14)}</button><div role="radiogroup" style="display:inline-flex; gap:2px; padding:2px; background:${t.muted}; border:1px solid ${t.border}; border-radius:6px">${['15m', '1h', '1d'].map(k => `<button class="btn mono" style="height:34px; border:none; border-radius:4px; padding:0 10px; background:${k === '1h' ? t.surface : 'transparent'}; color:${k === '1h' ? t.textHi : t.textMuted}">${k}</button>`).join('')}</div></div>
    <div style="display:flex; gap:8px; align-items:center; justify-content:space-between">${stamp(t, { mobile: true })}<button class="btn" aria-label="Atualizar" style="width:40px; padding:0; height:32px">${ic.refresh(16)}</button></div>
  </div>
  <section class="card" style="margin:10px 12px 0; position:relative; overflow:hidden; height:430px; flex:none">
    ${chartSvg(t, 364, 430, { mobile: true, show: 48, panes: ['rsi'], crossAt: 0.58, forecast: true })}
    ${legend(t, { mobile: true, rows: [['SMA 20', t.sma20, '113.512', ''], ['SMA 50', t.sma50, '112.981', '']] })}
  </section>
  <div style="padding:10px 12px 80px; flex:none">${kpiStrip(t, { mobile: true })}</div>
  <div style="position:absolute; left:0; right:0; bottom:0; display:flex; justify-content:space-around; align-items:center; height:64px; padding-bottom:max(8px, env(safe-area-inset-bottom)); background:${t.surface}; border-top:1px solid ${t.border}">
    ${[['Dashboard', ic.trend(20), true], ['Mercado', ic.table(20), false]].map(([l, i, a]) => `<a href="#" aria-current="${a ? 'page' : 'false'}" class="btn ghost" style="flex-direction:column; gap:2px; height:48px; min-width:72px; font-size:11px; color:${a ? t.primary : t.textMuted}; text-decoration:none">${i}<span>${l}</span></a>`).join('')}<button class="btn ghost" aria-haspopup="dialog" style="flex-direction:column; gap:2px; height:48px; min-width:72px; font-size:11px; color:${t.textMuted}">${ic.sliders(20)}<span>Indicadores</span></button>
  </div>
  <div style="position:absolute; right:12px; bottom:78px; width:1px; height:1px"></div>`;
  return wrap(t, 'Dashboard mobile', body, { w: W, h: H, mode });
}

function mobileDrawer(mode) {
  const t = T[mode]; const W = 390, H = 844;
  const body = `
  ${header(t, { mobile: true, mode })}
  <div style="position:absolute; inset:0; background:rgba(0,0,0,.45)"></div>
  <div class="card" role="dialog" aria-label="Indicadores" style="position:absolute; left:0; right:0; bottom:0; border-radius:12px 12px 0 0; padding:8px 12px 20px; display:flex; flex-direction:column; gap:4px">
    <div style="width:40px; height:4px; border-radius:999px; background:${t.accented}; margin:2px auto 8px"></div>
    <div style="display:flex; justify-content:space-between; align-items:center; padding:0 4px 8px"><span style="font-weight:600; color:${t.textHi}; font-size:15px">Indicadores</span><button class="btn ghost" aria-label="Fechar" style="width:36px; padding:0">${ic.x(18)}</button></div>
    ${[['SMA 20', t.sma20, true, 'solid'], ['SMA 50', t.sma50, true, 'solid'], ['SMA 200', t.sma200, false, 'solid'], ['EMA 12', t.ema12, false, 'dash'], ['EMA 26', t.ema26, false, 'dash'], ['Bollinger 20·2', t.bb, false, 'dot'], ['Volume', t.textDim, true, 'solid'], ['RSI 14', t.rsi, true, 'solid'], ['MACD 12·26·9', t.sma20, false, 'solid']].map(([l, c, on, st]) => `<label style="display:flex; align-items:center; gap:12px; height:44px; padding:0 4px; border-bottom:1px solid ${t.borderMuted}"><span style="width:20px; height:0; border-top:2px ${st === 'dash' ? 'dashed' : st === 'dot' ? 'dotted' : 'solid'} ${c}"></span><span style="flex:1; font-size:14px; color:${on ? t.text : t.textMuted}">${l}</span><span role="switch" tabindex="0" aria-checked="${on}" style="width:40px; height:24px; border-radius:999px; background:${on ? t.primary : t.accented}; position:relative; display:inline-block"><i style="position:absolute; top:3px; ${on ? 'right:3px' : 'left:3px'}; width:18px; height:18px; border-radius:999px; background:#fff; display:block"></i></span></label>`).join('')}
    <div class="hint" style="padding:10px 4px 0; display:flex; gap:6px">${ic.info(14)}<span>Linhas começam só depois da janela de cálculo (warm-up).</span></div>
  </div>`;
  return wrap(t, 'Indicadores (drawer mobile)', body, { w: W, h: H, mode });
}

function mercado(mode) {
  const t = T[mode]; const W = 1440, H = 900;
  const rows = [
    ['BTCUSDT', '113.512,3', '+2.048,9', '+1,84', '112.877,4', '111.463,4', '114.120,0', '110.902,1', '113.510,0', '113.512,9', '38.412', '4,33 bi', '4,21 mi'],
    ['ETHUSDT', '4.312,9', '−26,9', '−0,62', '4.330,1', '4.339,8', '4.402,0', '4.255,3', '4.312,5', '4.313,1', '612.440', '2,65 bi', '3,02 mi'],
    ['SOLUSDT', '186,40', '+5,62', '+3,11', '184,10', '180,78', '189,90', '179,20', '186,38', '186,41', '9,81 mi', '1,81 bi', '1,44 mi'],
    ['XRPUSDT', '3,0120', '−0,0320', '−1,05', '3,0410', '3,0440', '3,1020', '2,9800', '3,0118', '3,0122', '402 mi', '1,22 bi', '0,88 mi'],
    ['BNBUSDT', '842,10', '+1,70', '+0,20', '840,50', '840,40', '851,00', '833,20', '842,00', '842,20', '1,21 mi', '1,02 bi', '0,61 mi'],
    ['DOGEUSDT', '0,2310', '0,0000', '+0,00', '0,2298', '0,2310', '0,2361', '0,2255', '0,2309', '0,2311', '3,9 bi', '896 mi', '0,72 mi'],
    ['ADAUSDT', '0,9120', '−0,0210', '−2,25', '0,9210', '0,9330', '0,9440', '0,9010', '0,9119', '0,9122', '712 mi', '656 mi', '0,41 mi'],
    ['LINKUSDT', '24,18', '+0,91', '+3,91', '23,80', '23,27', '24,40', '23,05', '24,17', '24,19', '21,4 mi', '509 mi', '0,33 mi'],
    ['PEPEUSDT', '—', '—', '—', '—', '—', '—', '—', '—', '—', '—', '—', '—'],
    ['AVAXUSDT', '26,05', '−0,40', '−1,51', '26,30', '26,45', '26,90', '25,80', '26,04', '26,06', '8,2 mi', '216 mi', '0,19 mi'],
    ['TRXUSDT', '0,3520', '+0,0030', '+0,86', '0,3505', '0,3490', '0,3560', '0,3470', '0,3519', '0,3521', '590 mi', '207 mi', '0,22 mi'],
    ['SUIUSDT', '3,842', '+0,210', '+5,78', '3,760', '3,632', '3,900', '3,601', '3,841', '3,843', '51,2 mi', '193 mi', '0,27 mi'],
    ['LTCUSDT', '118,40', '−1,10', '−0,92', '118,90', '119,50', '121,20', '117,30', '118,38', '118,42', '1,5 mi', '178 mi', '0,12 mi'],
    ['DOTUSDT', '4,210', '−0,080', '−1,86', '4,250', '4,290', '4,330', '4,180', '4,209', '4,211', '36,8 mi', '156 mi', '0,10 mi'],
    ['BCHUSDT', '612,3', '+4,1', '+0,67', '610,0', '608,2', '618,0', '604,5', '612,1', '612,5', '0,22 mi', '135 mi', '0,08 mi'],
    ['NEARUSDT', '2,980', '+0,050', '+1,71', '2,955', '2,930', '3,010', '2,910', '2,979', '2,981', '41,0 mi', '122 mi', '0,09 mi'],
  ];
  const cols = ['Ativo', 'Último', 'Var. 24h', 'Var. %', 'Preço médio', 'Abertura', 'Máxima', 'Mínima', 'Bid', 'Ask', 'Volume (base)', 'Volume (USDT) ▼', 'Trades'];
  const body = `
  ${header(t, { active: 'mercado', mode })}
  <div style="display:flex; align-items:flex-end; justify-content:space-between; padding:20px 24px 12px; gap:16px; flex-wrap:wrap">
    <div><h1 style="margin:0; text-wrap:balance; font-size:20px; font-weight:600; letter-spacing:-.01em; color:${t.textHi}">Mercado · resumo 24h</h1><p class="hint" style="margin:4px 0 0">Top 20 pares USDT por volume. Clique em um ativo para abri-lo no dashboard.</p></div>
    <div style="display:flex; gap:8px; align-items:center">
      <div class="input" style="height:32px; width:220px; font-size:13px"><span style="color:${t.textDim}">${ic.search(14)}</span><span class="ph">Filtrar ativo…</span></div>
      <span class="mono" style="display:inline-flex; align-items:center; gap:8px; height:32px; padding:0 10px; border:1px solid ${t.border}; border-radius:6px; background:${t.surface}; color:${t.textMuted}; font-size:11px; white-space:nowrap"><span style="width:7px; height:7px; border-radius:999px; background:${t.up}"></span><span style="font-weight:500; letter-spacing:.06em">SNAPSHOT</span><span style="color:${t.border}">|</span><span>Resumo 24h: 19 ago 14:00 UTC · há 12 min · atualiza de hora em hora</span></span>
      <button class="btn">${ic.refresh(14)}<span>Atualizar</span></button>
    </div>
  </div>
  <section class="card" style="margin:0 24px; overflow:hidden">
    <div style="overflow-x:auto">
    <table class="tbl" aria-label="Resumo 24h por ativo">
      <thead><tr>${cols.map((c, i) => `<th scope="col" tabindex="0" aria-sort="${i === 11 ? 'descending' : 'none'}" style="${i === 11 ? `color:${t.textHi}` : ''}; ${i === 0 ? 'position:sticky; left:0; background:' + t.surface : ''}">${c}</th>`).join('')}</tr></thead>
      <tbody>${rows.map((r, ri) => `<tr class="${ri === 0 ? 'sel' : ri === 2 ? 'hover' : ''}" tabindex="0">${r.map((v, ci) => { let style = ci === 0 ? `position:sticky; left:0; background:${ri === 0 ? t.primarySoft : ri === 2 ? t.muted : t.surface}; font-weight:500; color:${t.textHi}` : ''; let cell = v; if (ci === 3 && v !== '—') { const up = v.startsWith('+') && v !== '+0,00'; const dn = v.startsWith('−'); cell = `<span style="color:${up ? t.up : dn ? t.down : t.textMuted}">${up ? '▲ ' : dn ? '▼ ' : ''}${v} %</span>`; } if (ci === 2 && v !== '—') { const up = v.startsWith('+'); const dn = v.startsWith('−'); cell = `<span style="color:${up ? t.up : dn ? t.down : t.textMuted}">${v}</span>`; } if (v === '—') cell = `<span style="color:${t.textDim}" title="Sem snapshot recente para este ativo">—</span>`; if (ci === 0 && ri === 8) cell += ` <span class="hint mono" style="font-size:10px; font-weight:400">sem dados</span>`; return `<td style="${style}">${cell}</td>`; }).join('')}</tr>`).join('')}</tbody>
    </table></div>
    <div style="display:flex; justify-content:space-between; padding:10px 12px; border-top:1px solid ${t.border}" class="hint"><span>20 ativos (16 visíveis, rola) · ordenado por volume (USDT) desc · cabeçalhos ordenáveis (Enter/Espaço)</span><span class="mono">▲ alta · ▼ baixa · sem seta = sem variação · — = sem dados</span></div>
  </section>`;
  return wrap(t, 'Mercado', body, { w: W, h: H, mode });
}

function mercadoMobile(mode) {
  const t = T[mode]; const W = 390, H = 844;
  const rows = [['BTCUSDT', 'Bitcoin', '113.512,3', '+1,84', '4,33 bi', true], ['ETHUSDT', 'Ethereum', '4.312,9', '−0,62', '2,65 bi'], ['SOLUSDT', 'Solana', '186,40', '+3,11', '1,81 bi'], ['XRPUSDT', 'XRP', '3,0120', '−1,05', '1,22 bi'], ['BNBUSDT', 'BNB', '842,10', '+0,20', '1,02 bi'], ['DOGEUSDT', 'Dogecoin', '0,2310', '+0,00', '896 mi'], ['ADAUSDT', 'Cardano', '0,9120', '−2,25', '656 mi'], ['PEPEUSDT', 'Pepe', '—', '—', '—'], ['LINKUSDT', 'Chainlink', '24,18', '+3,91', '509 mi']];
  const body = `
  ${header(t, { mobile: true, mode })}
  <div style="padding:12px 12px 8px; display:flex; flex-direction:column; gap:8px">
    <div style="display:flex; justify-content:space-between; align-items:baseline"><span style="font-size:17px; font-weight:600; color:${t.textHi}">Mercado</span><span class="hint mono" style="font-size:11px">24h · 14:00 UTC · há 12 min</span></div>
    <div style="display:flex; gap:8px"><div class="input" style="flex:1; height:40px"><span style="color:${t.textDim}">${ic.search(14)}</span><span class="ph">Filtrar ativo…</span></div><button class="btn" style="height:40px">${ic.sort(14)}<span>Volume</span>${ic.chevron(14)}</button></div>
  </div>
  <div class="card" style="margin:0 12px; overflow:hidden">
    ${rows.map(([s, n, p, v, vol, sel]) => { const up = v.startsWith('+') && v !== '+0,00'; const dn = v.startsWith('−'); const nul = v === '—'; return `<a href="#" style="display:flex; align-items:center; justify-content:space-between; padding:10px 14px; min-height:56px; border-bottom:1px solid ${t.borderMuted}; background:${sel ? t.primarySoft : 'transparent'}; text-decoration:none; color:inherit"><span style="display:flex; flex-direction:column"><span class="mono" style="font-weight:500; color:${t.textHi}; font-size:14px">${s}</span><span class="hint">${n} · vol ${vol}</span></span><span style="display:flex; flex-direction:column; align-items:flex-end"><span class="mono" style="font-size:14px; color:${nul ? t.textDim : t.textHi}">${p}</span><span class="mono" style="font-size:12px; color:${nul ? t.textDim : up ? t.up : dn ? t.down : t.textMuted}">${nul ? 'sem dados' : `${up ? '▲ ' : dn ? '▼ ' : ''}${v} %`}</span></span></a>`; }).join('')}
  </div>
  <div style="position:absolute; left:0; right:0; bottom:0; display:flex; justify-content:space-around; align-items:center; height:64px; padding-bottom:max(8px, env(safe-area-inset-bottom)); background:${t.surface}; border-top:1px solid ${t.border}">
    ${[['Dashboard', ic.trend(20), false], ['Mercado', ic.table(20), true], ['Previsões', ic.sparkle(20), false]].map(([l, i, a]) => `<a href="#" aria-current="${a ? 'page' : 'false'}" ${l === 'Previsões' ? 'aria-disabled="true"' : ''} class="btn ghost" style="flex-direction:column; gap:2px; height:48px; min-width:72px; font-size:11px; color:${a ? t.primary : t.textMuted}; text-decoration:none; ${l === 'Previsões' ? 'opacity:.5' : ''}">${i}<span>${l}</span></a>`).join('')}
  </div>`;
  return wrap(t, 'Mercado mobile', body, { w: W, h: H, mode });
}

// ---------- auth ----------
function authShell(t, mode, inner, { w = 480, h = 640, banner = '' } = {}) {
  const body = `
  <div style="display:flex; flex-direction:column; align-items:center; justify-content:center; flex:1; padding:32px 24px; gap:20px">
    ${banner}
    <div style="display:flex; align-items:center; gap:10px"><span style="width:32px; height:32px; border-radius:8px; background:${t.textHi}; color:${t.bg}; display:inline-flex; align-items:center; justify-content:center; font:600 14px ${MONO}">cf</span><span style="font-weight:600; font-size:15px; color:${t.textHi}">crypto forecasting</span></div>
    <div class="card" style="width:100%; max-width:400px; padding:28px 28px 24px; display:flex; flex-direction:column; gap:16px">${inner}</div>
    <p class="hint mono" style="margin:0; font-size:11px">Dados da Binance · snapshots diários · horários em UTC</p>
  </div>`;
  return wrap(t, 'Auth', body, { w, h, mode });
}
const field = (t, label, ph, { type = 'text', icon = null, err = '', right = '' } = {}) => { const id = 'f-' + label.toLowerCase().replace(/[^a-z]+/g, '-'); return `<div><div style="display:flex; justify-content:space-between; align-items:baseline"><label class="label" for="${id}">${label}</label>${right}</div><div class="input" id="${id}" role="textbox" tabindex="0" style="${err ? `border-color:${t.danger}` : ''}">${icon ? `<span style="color:${t.textDim}">${icon}</span>` : ''}<span class="${ph.startsWith('•') || ph.includes('@') ? '' : 'ph'}" style="flex:1">${ph}</span>${type === 'password' ? `<button type="button" aria-label="Mostrar senha" aria-pressed="false" style="display:inline-flex; align-items:center; justify-content:center; width:28px; height:28px; margin-right:-6px; border:none; background:transparent; color:${t.textDim}; cursor:pointer; border-radius:4px">${ic.eye(16)}</button>` : ''}</div>${err ? `<p style="margin:6px 0 0; font-size:12px; color:${t.danger}; display:flex; gap:6px; align-items:center">${ic.alert(14)}${err}</p>` : ''}</div>`; };

function authLogin(mode, variant = 'default') {
  const t = T[mode];
  const expired = variant === 'expired'; const errored = variant === 'error';
  const banner = expired ? `<div role="status" style="width:100%; max-width:400px; display:flex; gap:10px; align-items:flex-start; padding:10px 12px; border-radius:6px; border:1px solid ${t.border}; background:${t.surface}; color:${t.textMuted}; font-size:13px"><span style="color:${t.textDim}; flex:none; margin-top:1px">${ic.clock(16)}</span><span>Sua sessão expirou. Entre de novo para continuar — você voltará para onde estava.</span></div>` : '';
  const inner = `
    <div><h1 style="margin:0; text-wrap:balance; font-size:20px; font-weight:600; letter-spacing:-.01em; color:${t.textHi}">Entrar</h1><p class="hint" style="margin:4px 0 0">Use o e-mail e a senha da sua conta.</p></div>
    ${errored ? `<div role="alert" style="display:flex; gap:8px; align-items:flex-start; padding:10px 12px; border-radius:6px; background:${t.dangerBg}; color:${t.danger}; font-size:13px"><span style="flex:none; margin-top:1px">${ic.xcircle(16)}</span><span>E-mail ou senha inválidos.</span></div>` : ''}
    ${field(t, 'E-mail', 'gabriel@exemplo.com', { icon: ic.mail(16) })}
    ${field(t, 'Senha', '••••••••••', { type: 'password', icon: ic.lock(16), right: `<a href="#" style="font-size:12px">Esqueci a senha</a>` })}
    <button class="btn primary lg block">Entrar</button>
    <p class="hint" style="margin:0; text-align:center">Não tem conta? <a href="#">Criar conta</a></p>`;
  return authShell(t, mode, inner, { banner });
}
function authSignup(mode) {
  const t = T[mode];
  const inner = `
    <div><h1 style="margin:0; text-wrap:balance; font-size:20px; font-weight:600; letter-spacing:-.01em; color:${t.textHi}">Criar conta</h1><p class="hint" style="margin:4px 0 0">Você receberá um link para confirmar o e-mail.</p></div>
    ${field(t, 'E-mail', 'voce@exemplo.com', { icon: ic.mail(16) })}
    ${field(t, 'Senha', 'mínimo 8 caracteres', { type: 'password', icon: ic.lock(16) })}
    <div style="display:flex; gap:4px; margin-top:-8px" aria-hidden="true"><i style="flex:1; height:3px; border-radius:2px; background:${t.up}"></i><i style="flex:1; height:3px; border-radius:2px; background:${t.up}"></i><i style="flex:1; height:3px; border-radius:2px; background:${t.accented}"></i><i style="flex:1; height:3px; border-radius:2px; background:${t.accented}"></i></div>
    <p class="hint" style="margin:-10px 0 0">Força: razoável · use 12+ caracteres com números e símbolos</p>
    ${field(t, 'Confirmar senha', '••••••••••', { type: 'password', icon: ic.lock(16) })}
    <button class="btn primary lg block">Criar conta</button>
    <p class="hint" style="margin:0; text-align:center">Já tem conta? <a href="#">Entrar</a></p>`;
  return authShell(t, mode, inner);
}
function authConfirm(mode) {
  const t = T[mode];
  const inner = `
    <div style="display:flex; flex-direction:column; align-items:center; text-align:center; gap:12px; padding:8px 0 4px">
      <span style="width:48px; height:48px; border-radius:12px; background:${t.primarySoft}; color:${t.primary}; display:inline-flex; align-items:center; justify-content:center">${ic.inbox(24)}</span>
      <h1 style="margin:0; text-wrap:balance; font-size:20px; font-weight:600; letter-spacing:-.01em; color:${t.textHi}">Verifique seu e-mail</h1>
      <p style="margin:0; color:${t.textMuted}">Se este e-mail for novo, enviamos um link de confirmação para <span class="mono" style="color:${t.text}">voce@exemplo.com</span>. O link vale por 24 horas.</p>
    </div>
    <div class="hint" style="display:flex; gap:8px; align-items:flex-start; padding:10px 12px; border-radius:6px; background:${t.muted}"><span style="flex:none; color:${t.textDim}; margin-top:1px">${ic.info(14)}</span><span>Não chegou? Confira o spam. Você pode pedir outro link em <span class="mono">0:42</span>.</span></div>
    <button class="btn lg block" disabled style="opacity:.6">Reenviar link</button>
    <p class="hint" style="margin:0; text-align:center"><a href="#">Voltar para entrar</a></p>`;
  return authShell(t, mode, inner);
}
function authForgot(mode) {
  const t = T[mode];
  const inner = `
    <div><a href="#" class="hint" style="display:inline-flex; align-items:center; gap:4px; margin-bottom:12px">${ic.back(14)}Voltar</a><h1 style="margin:0; text-wrap:balance; font-size:20px; font-weight:600; letter-spacing:-.01em; color:${t.textHi}">Esqueci a senha</h1><p class="hint" style="margin:4px 0 0">Informe o e-mail da conta. Enviaremos um link para criar uma nova senha.</p></div>
    ${field(t, 'E-mail', 'voce@exemplo.com', { icon: ic.mail(16) })}
    <button class="btn primary lg block">Enviar link</button>
    <div role="status" style="display:flex; gap:8px; align-items:flex-start; padding:10px 12px; border-radius:6px; background:${t.muted}; color:${t.textMuted}; font-size:13px"><span style="flex:none; margin-top:1px; color:${t.up}">${ic.check(16)}</span><span>Se existir uma conta com este e-mail, você receberá um link em instantes.</span></div>`;
  return authShell(t, mode, inner, { h: 560 });
}
function authReset(mode) {
  const t = T[mode];
  const inner = `
    <div><h1 style="margin:0; text-wrap:balance; font-size:20px; font-weight:600; letter-spacing:-.01em; color:${t.textHi}">Redefinir senha</h1><p class="hint" style="margin:4px 0 0">Crie uma nova senha para <span class="mono">voce@exemplo.com</span>.</p></div>
    ${field(t, 'Nova senha', '••••••••••••', { type: 'password', icon: ic.lock(16) })}
    ${field(t, 'Confirmar nova senha', '••••••••••', { type: 'password', icon: ic.lock(16), err: 'As senhas não coincidem.' })}
    <button class="btn primary lg block">Salvar nova senha</button>
    <div class="hint" style="display:flex; gap:8px; align-items:flex-start; padding:10px 12px; border-radius:6px; background:${t.muted}"><span style="flex:none; color:${t.textDim}; margin-top:1px">${ic.info(14)}</span><span>Link expirado ou inválido? <a href="#">Peça um novo</a>.</span></div>`;
  return authShell(t, mode, inner, { h: 560 });
}

// ---------- estados ----------
function estados(mode) {
  const t = T[mode]; const W = 1440, H = 900; const pw = (W - 48 - 16 * 2) / 3, ph = 340;
  const panel = (title, sub, inner) => `<div style="display:flex; flex-direction:column; gap:8px; width:${pw}px"><div><div style="font-weight:600; color:${t.textHi}">${title}</div><div class="hint">${sub}</div></div><div class="card" style="height:${ph}px; position:relative; overflow:hidden">${inner}</div></div>`;
  const center = (icon, h, p, btn = '') => `<div style="position:absolute; inset:0; display:flex; flex-direction:column; align-items:center; justify-content:center; text-align:center; gap:8px; padding:24px"><span style="color:${t.textDim}">${icon}</span><div style="font-weight:600; color:${t.textHi}">${h}</div><p class="hint" style="margin:0; max-width:300px">${p}</p>${btn}</div>`;
  const skel = `<div style="position:absolute; left:12px; top:10px; display:flex; gap:8px"><span class="sk" style="width:72px; height:12px"></span><span class="sk" style="width:160px; height:12px"></span></div>${chartSvg(t, pw - 2, ph - 2, { skeleton: true, panes: ['rsi'], crossAt: 0, cut: false, forecast: false })}<div class="hint mono" style="position:absolute; left:12px; bottom:10px; font-size:11px">Carregando BTCUSDT · 1h…</div>`;
  const warm = `${chartSvg(t, pw - 2, ph - 2, { show: 60, total: 70, overlays: ['sma20', 'sma50'], panes: ['rsi'], crossAt: 0, cut: true, forecast: false, seed: 11, padTop: 108 })}${legend(t, { tf: '1h', mobile: true, rows: [['SMA 20', t.sma20, '111.204,0', ''], ['SMA 50', t.sma50, '—', 'warm-up · a partir de 04 ago'], ['SMA 200', t.sma200, '—', 'warm-up · faltam 140 velas']] })}`;
  const stale = `<div style="padding:12px; display:flex; flex-direction:column; gap:10px">${stamp(t, { state: 'stale', mobile: true })}<div style="display:flex; gap:8px; align-items:flex-start; padding:10px 12px; border-radius:6px; background:${t.warnBg}; color:${t.warn}; font-size:13px"><span style="flex:none; margin-top:1px">${ic.alert(16)}</span><span><strong>Dados mais antigos que o esperado.</strong> Os candles deveriam ter sido atualizados há ~7 h (00:05 UTC). O gráfico continua utilizável; os valores podem não refletir o último dia. <a href="#" style="color:${t.warn}; text-decoration:underline">Tentar novamente</a></span></div><div class="hint">Regra: candles/indicadores &gt; 26 h → aviso · resumo 24h &gt; 2 h → aviso. O gráfico não fica bloqueado.</div></div>`;
  const body = `
  <div style="padding:20px 24px 8px"><h1 style="margin:0; text-wrap:balance; font-size:20px; font-weight:600; letter-spacing:-.01em; color:${t.textHi}">Estados do bloco de gráfico</h1><p class="hint" style="margin:4px 0 0">Mesmo container (card) em todos os estados — nada muda de lugar. Microcopy exato da spec.</p></div>
  <div style="display:flex; gap:16px; padding:12px 24px; flex-wrap:wrap">
    ${panel('1 · Carregando', 'skeleton no lugar do gráfico; legenda com barras; a toolbar fica ativa', skel)}
    ${panel('2 · Vazio', 'API devolve 200 [] — ativo na lista sem dados recentes', center(ic.layers(24), 'Sem dados para PEPEUSDT em 1h', 'Este ativo está na lista dos top 20, mas ainda não tem candles neste timeframe. Tente outro timeframe ou volte depois da próxima coleta (00:05 UTC).', `<div style="display:flex; gap:8px; margin-top:6px"><button class="btn" style="height:28px">Ver em 1d</button><button class="btn ghost" style="height:28px">Escolher outro ativo</button></div>`))}
    ${panel('3 · Erro', 'API indisponível / 5xx / rede', center(`<span style="color:${t.danger}">${ic.xcircle(24)}</span>`, 'Não foi possível carregar o gráfico', 'A API não respondeu. Tente de novo em alguns segundos.', `<div style="display:flex; gap:8px; margin-top:6px; align-items:center"><button class="btn primary" style="height:28px">${ic.refresh(14)}Tentar novamente</button><span class="hint mono" style="font-size:11px">GET /klines/1h · 503</span></div>`))}
    ${panel('4 · Warm-up parcial', 'linhas começam onde o indicador existe; legenda explica; nunca zero', warm)}
    ${panel('5 · Dados velhos (stale)', 'selo em âmbar + alerta inline; o gráfico continua visível', stale)}
    ${panel('6 · Sessão expirada', '401 após refresh falho → redirect para /login?reason=expired', center(ic.clock(24), 'Redirecionando para entrar…', 'Toast discreto: “Sessão expirada. Entre de novo para continuar.” O ativo e o timeframe ficam na URL e são restaurados após o login.'))}
  </div>`;
  return wrap(t, 'Estados', body, { w: W, h: H, mode });
}

// ---------- previsões slot ----------
function previsoes(mode) {
  const t = T[mode]; const W = 960, H = 520;
  const body = `
  <div style="padding:20px 24px 8px"><h1 style="margin:0; text-wrap:balance; font-size:20px; font-weight:600; letter-spacing:-.01em; color:${t.textHi}">Reserva para previsões (marco 3)</h1><p class="hint" style="margin:4px 0 0">Não detalhar agora. A linha de corte já existe hoje; a faixa projetada e o card de métricas aparecem quando <span class="mono">/forecasts</span> existir.</p></div>
  <div style="display:flex; gap:16px; padding:12px 24px">
    <div class="card" style="flex:1; position:relative; overflow:hidden; height:400px">${chartSvg(t, 620, 400, { panes: [], overlays: ['sma20'], crossAt: 0, show: 70, total: 90, forecast: true, seed: 3 })}${legend(t, { rows: [['SMA 20', t.sma20, '113.512,3', ''], ['Previsão 7d', t.primary, 'faixa 80 %', 'modelo v0.3']] })}</div>
    <div style="width:272px; display:flex; flex-direction:column; gap:12px">
      <div class="card" style="padding:14px 16px; display:flex; flex-direction:column; gap:10px"><div style="display:flex; justify-content:space-between; align-items:center"><span style="font-weight:600; color:${t.textHi}">Modelo</span><span class="chip">Prophet · v0.3</span></div><div style="display:grid; grid-template-columns:repeat(2, minmax(0,1fr)); gap:10px">${[['MAE', '412,3', 'USDT'], ['RMSE', '588,9', 'USDT'], ['Horizonte', '7 d', ''], ['Treinado em', '19 ago', '00:40 UTC']].map(([l, v, s]) => `<div style="display:flex; flex-direction:column"><span class="hint" style="font-size:11px">${l}</span><span class="mono" style="font-size:16px; font-weight:500; color:${t.textHi}">${v}</span><span class="hint mono" style="font-size:11px">${s}</span></div>`).join('')}</div></div>
      <div class="hint" style="display:flex; gap:6px; align-items:flex-start">${ic.info(14)}<span>Toggle "Previsão" entra no painel de Indicadores, grupo "Modelo". Aba Previsões na nav lista rodadas e métricas por ativo.</span></div>
    </div>
  </div>`;
  return wrap(t, 'Previsões (reserva)', body, { w: W, h: H, mode });
}

// ---------- tokens / sistema ----------
function tokensBoard() {
  const W = 1400, H = 980; const lt = T.light, dk = T.dark;
  const sw = (t, name, hex, txt) => `<div style="display:flex; flex-direction:column; gap:6px; width:110px"><div style="height:44px; border-radius:6px; background:${hex}; border:1px solid ${t.border}"></div><span style="font-size:12px; color:${t.text}">${name}</span><span class="mono" style="font-size:11px; color:${t.textMuted}">${hex}</span></div>`;
  const half = (t, mode) => `<div style="flex:1; background:${t.bg}; color:${t.text}; padding:24px; display:flex; flex-direction:column; gap:20px">
    <div><div class="eyebrow" style="color:${t.textMuted}">${mode}</div><h2 style="margin:2px 0 0; font-size:18px; font-weight:600; color:${t.textHi}">Paleta de chrome</h2></div>
    <div style="display:flex; gap:12px; flex-wrap:wrap">${sw(t, 'bg', t.bg)}${sw(t, 'surface', t.surface)}${sw(t, 'muted', t.muted)}${sw(t, 'border', t.border)}${sw(t, 'text', t.text)}${sw(t, 'text-muted', t.textMuted)}${sw(t, 'text-dimmed', t.textDim)}${sw(t, 'primary', t.primary)}${sw(t, 'warning', t.warn)}${sw(t, 'danger', t.danger)}</div>
    <div><h2 style="margin:0; font-size:18px; font-weight:600; color:${t.textHi}">Séries do gráfico</h2><div class="hint" style="color:${t.textMuted}">validadas com dataviz/validate_palette.js · ordem fixa</div></div>
    <div style="display:flex; gap:12px; flex-wrap:wrap">${sw(t, 'alta', t.up)}${sw(t, 'baixa', t.down)}${sw(t, 'SMA 20', t.sma20)}${sw(t, 'SMA 50', t.sma50)}${sw(t, 'SMA 200', t.sma200)}${sw(t, 'EMA 12', t.ema12)}${sw(t, 'EMA 26', t.ema26)}${sw(t, 'Bollinger', t.bb)}${sw(t, 'RSI', t.rsi)}</div>
    <div class="card" style="background:${t.surface}; border-color:${t.border}; padding:16px; display:flex; flex-direction:column; gap:12px">
      <div class="eyebrow" style="color:${t.textMuted}">Tipografia</div>
      <div style="font:600 20px ${SANS}; color:${t.textHi}; letter-spacing:-.01em">IBM Plex Sans 600 · títulos</div>
      <div style="font:400 13px/1.45 ${SANS}; color:${t.text}">IBM Plex Sans 400 · texto de interface, rótulos, descrições, mensagens de estado.</div>
      <div class="mono" style="font-size:22px; font-weight:500; color:${t.textHi}">113.512,3 <span style="font-size:13px; color:${t.up}">▲ +1,84 %</span></div>
      <div class="mono" style="font-size:13px; color:${t.text}">IBM Plex Mono · tabular-nums · 19 ago 00:00 UTC · 0,0031 %</div>
      <div class="eyebrow" style="color:${t.textMuted}">eyebrow · mono 11 · caixa alta · +0.06em</div>
    </div>
    <div style="display:flex; gap:10px; align-items:center; flex-wrap:wrap">
      <button class="btn primary" style="background:${t.primary}; border-color:${t.primary}; color:${t.onPrimary}">Primário</button><button class="btn" style="background:${t.surface}; border-color:${t.border}; color:${t.text}">Secundário</button><button class="btn ghost" style="color:${t.textMuted}">Ghost</button><span class="chip on" style="background:${t.primarySoft}; border-color:${t.primary}; color:${t.primary}">chip ativo</span><span class="chip" style="background:${t.surface}; border-color:${t.border}; color:${t.textMuted}">chip</span><span class="btn focus" style="background:${t.surface}; border-color:${t.border}; color:${t.text}; outline-color:${t.primary}">foco visível</span>
    </div>
  </div>`;
  const body = `<div style="display:flex; flex:1">${half(lt, 'light')}${half(dk, 'dark')}</div>`;
  return `<!doctype html>
<html><head><meta charset="utf-8"><script src="./support.js"></script></head><body><x-dc><helmet>${FONTS}<style>${baseCss(lt)} .btn{font-family:${SANS}}</style></helmet>
<div aria-label="Tokens" style="width:${W}px; height:${H}px; display:flex; font-family:${SANS}; font-size:13px; overflow:hidden">${body}</div>
</x-dc><script data-dc-script data-props='{"$preview":{"width":${W},"height":${H}}}'>class Component extends DCLogic { renderVals() { return {}; } }</script></body></html>`;
}

function componentes(mode) {
  const t = T[mode]; const W = 1440, H = 1040;
  const box = (title, sub, inner, w = 440) => `<div style="display:flex; flex-direction:column; gap:8px; width:${w}px"><div><div style="font-weight:600; color:${t.textHi}">${title}</div><div class="hint mono" style="font-size:11px">${sub}</div></div><div class="card" style="padding:14px; display:flex; flex-direction:column; gap:10px; position:relative; min-height:120px">${inner}</div></div>`;
  const body = `
  <div style="padding:20px 24px 8px"><h1 style="margin:0; text-wrap:balance; font-size:20px; font-weight:600; letter-spacing:-.01em; color:${t.textHi}">Inventário de componentes · mapeado para Nuxt UI v4</h1><p class="hint" style="margin:4px 0 0">Detalhes (props, estados, a11y) em docs/design/components.md</p></div>
  <div style="display:flex; gap:16px; padding:12px 24px; flex-wrap:wrap; align-content:flex-start">
    ${box('SymbolSelector', 'USelectMenu · searchable · :items=/symbols · v-model=query.symbol', `<button class="btn" style="width:260px; justify-content:space-between"><span style="display:inline-flex; gap:8px; align-items:center"><span style="color:${t.textDim}">${ic.search(14)}</span><span class="mono" style="font-weight:500; color:${t.textHi}">ETHUSDT</span><span class="hint">Ethereum / Tether</span></span>${ic.chevron(14)}</button><div class="hint">item: símbolo (mono 500) + nome + último/var% à direita · vazio: "Nenhum ativo encontrado" · skeleton enquanto /symbols carrega</div>`)}
    ${box('TimeframeToggle', 'UTabs (variant=pill, size=sm) ou URadioGroup visual · aria-pressed', `<div role="radiogroup" style="display:inline-flex; gap:2px; padding:2px; background:${t.muted}; border:1px solid ${t.border}; border-radius:6px; width:max-content">${['15m', '1h', '1d'].map(k => `<span class="btn mono" style="height:30px; border:none; border-radius:4px; padding:0 12px; background:${k === '1d' ? t.surface : 'transparent'}; color:${k === '1d' ? t.textHi : t.textMuted}">${k}</span>`).join('')}</div><div class="hint">teclado: ← → troca; subtítulo "1d · histórico completo" · "15m · últimos 7 dias"</div>`)}
    ${box('DataFreshnessBadge', 'UBadge/UTooltip · color=neutral|warning · variant=subtle', `<div style="display:flex; flex-direction:column; gap:8px; align-items:flex-start">${stamp(t)}${stamp(t, { state: 'stale' })}<span class="mono" style="display:inline-flex; align-items:center; gap:8px; height:32px; padding:0 10px; border:1px solid ${t.border}; border-radius:6px; color:${t.textMuted}; font-size:11px"><span class="sk" style="width:7px; height:7px; border-radius:999px"></span><span style="font-weight:500; letter-spacing:.06em">SNAPSHOT</span><span style="color:${t.border}">|</span><span class="sk" style="width:140px; height:10px; display:inline-block"></span></span></div>`)}
    ${box('IndicatorToggles', 'UCheckboxGroup (desktop) / USwitch em UDrawer (mobile) · useLocalStorage', `<div style="display:flex; gap:12px; flex-wrap:wrap">${[['SMA 20', t.sma20, true], ['EMA 12', t.ema12, false], ['Bollinger', t.bb, false]].map(([l, c, on]) => `<label style="display:inline-flex; align-items:center; gap:8px; height:32px"><span style="width:16px; height:16px; border-radius:4px; border:1px solid ${on ? t.primary : t.border}; background:${on ? t.primary : t.surface}; color:${t.onPrimary}; display:inline-flex; align-items:center; justify-content:center">${on ? ic.check(12) : ''}</span><span style="width:16px; border-top:2px ${l.startsWith('EMA') ? 'dashed' : l.startsWith('Boll') ? 'dotted' : 'solid'} ${c}"></span><span>${l}</span></label>`).join('')}</div><div class="hint">swatch = cor + estilo de traço real · grupo "Sobre o preço" / "Painéis abaixo" / (futuro) "Modelo"</div>`)}
    ${box('ChartLegend', 'componente próprio · absolute no canto · valores do crosshair', `<div style="position:relative; height:52px">${legend(t, { rows: [['SMA 20', t.sma20, '113.512,3', ''], ['SMA 50', t.sma50, '—', 'warm-up'], ['BB', t.bb, '114.4k / 112.6k', '']] })}</div><div class="hint">sem crosshair: mostra o último valor · null → "—" + nota "warm-up" · A/M/m/F = abertura/máx/mín/fechamento</div>`)}
    ${box('Stat tile (Resumo 24h)', 'UCard · grid 7 col desktop / scroll-x mobile', `<div style="display:flex; gap:0"><div style="display:flex; flex-direction:column; gap:2px; padding:6px 12px 6px 0; border-right:1px solid ${t.borderMuted}"><span class="hint" style="font-size:11px">Variação 24h</span><span class="mono up" style="font-size:14px; font-weight:500">▲ +2.048,9 · +1,84 %</span></div><div style="display:flex; flex-direction:column; gap:2px; padding:6px 12px"><span class="hint" style="font-size:11px">Bid / Ask</span><span class="mono" style="font-size:14px; font-weight:500; color:${t.textHi}">— / —</span><span class="hint mono" style="font-size:11px">sem snapshot</span></div></div><div class="hint">rótulo 11 · valor mono 14/500 · sub mono 11 · null → "—" nunca 0</div>`)}
    ${box('Tickers24hTable', 'UTable · sorting client-side · sticky 1ª coluna · @select → navigateTo(/?symbol=)', `<table class="tbl"><thead><tr><th scope="col">Ativo</th><th scope="col">Último</th><th scope="col" aria-sort="descending" style="color:${t.textHi}">Var. % ▼</th></tr></thead><tbody><tr class="sel"><td style="font-weight:500; color:${t.textHi}">SOLUSDT</td><td>186,40</td><td><span style="color:${t.up}">▲ +3,11 %</span></td></tr><tr><td style="font-weight:500; color:${t.textHi}">ADAUSDT</td><td>0,9120</td><td><span style="color:${t.down}">▼ −2,25 %</span></td></tr></tbody></table><div class="hint">linha focável (tabindex) · Enter abre · aria-sort no th · skeleton de 8 linhas · vazio: "Nenhum snapshot disponível"</div>`)}
    ${box('EmptyState / ErrorState', 'componentes próprios sobre UCard · ícone lucide 24 · título · texto · ações', `<div style="display:flex; gap:8px; align-items:center"><span style="color:${t.danger}">${ic.xcircle(20)}</span><div style="flex:1"><div style="font-weight:600; color:${t.textHi}">Não foi possível carregar o gráfico</div><div class="hint">A API não respondeu. Tente de novo em alguns segundos.</div></div><button class="btn primary" style="height:28px">${ic.refresh(14)}Tentar novamente</button></div>`)}
    ${box('Toast / Alert', 'useToast() (ações) · UAlert (inline, stale/erro)', `<div style="display:flex; flex-direction:column; gap:8px"><div class="card" style="padding:10px 12px; display:flex; gap:8px; align-items:center; box-shadow:${t.shadow}"><span style="color:${t.up}">${ic.check(16)}</span><span>Senha atualizada. Você já está conectado.</span></div><div style="display:flex; gap:8px; align-items:center; padding:10px 12px; border-radius:6px; background:${t.warnBg}; color:${t.warn}">${ic.alert(16)}<span>Dados mais antigos que o esperado.</span></div></div>`)}
    ${box('AuthCard / PasswordField', 'UCard + UForm + UFormField + UInput(type=password, trailing eye) · UAuthForm opcional', `${field(t, 'Senha', '••••••••', { type: 'password', icon: ic.lock(16) })}<div class="hint">erro abaixo do campo com ícone · mensagens genéricas (nunca "e-mail não existe") · botão com loading state</div>`)}
    ${box('App shell / nav', 'UHeader + UNavigationMenu (desktop) · barra inferior UNavigationMenu (mobile) · UDropdownMenu conta', `<div style="display:flex; gap:4px"><span style="display:inline-flex; align-items:center; gap:6px; height:32px; padding:0 10px; border-radius:6px; background:${t.muted}; color:${t.textHi}; font-weight:500">${ic.trend(16)}Dashboard</span><span style="display:inline-flex; align-items:center; gap:6px; height:32px; padding:0 10px; color:${t.textMuted}; font-weight:500">${ic.table(16)}Mercado</span><span style="display:inline-flex; align-items:center; gap:6px; height:32px; padding:0 10px; color:${t.textMuted}; font-weight:500; opacity:.75">${ic.sparkle(16)}Previsões <span class="mono" style="font-size:10px; padding:1px 6px; border-radius:999px; border:1px solid ${t.border}; color:${t.textDim}">EM BREVE</span></span></div><div class="hint">item disabled com badge — comunica roadmap sem levar a lugar nenhum · conta: e-mail, tema, "Velas de alta vazadas", Sair</div>`)}
  </div>`;
  return wrap(t, 'Componentes', body, { w: W, h: H, mode });
}

// ---------- write ----------
const files = {
  'Main.dc.html': dashboard('light', { title: 'Dashboard' }),
  'DashboardDark.dc.html': dashboard('dark'),
  'DashboardSeletor.dc.html': dashboard('light', { open: true }),
  'DashboardOnboarding.dc.html': dashboard('light', { onboarding: true, on: ['sma20', 'vol', 'rsi'], overlays: ['sma20'] }),
  'DashboardMobile.dc.html': dashboardMobile('light'),
  'DashboardMobileDark.dc.html': dashboardMobile('dark'),
  'IndicadoresDrawerMobile.dc.html': mobileDrawer('light'),
  'Mercado.dc.html': mercado('light'),
  'MercadoDark.dc.html': mercado('dark'),
  'MercadoMobile.dc.html': mercadoMobile('light'),
  'Estados.dc.html': estados('light'),
  'EstadosDark.dc.html': estados('dark'),
  'PrevisoesReserva.dc.html': previsoes('light'),
  'AuthLogin.dc.html': authLogin('light'),
  'AuthLoginErro.dc.html': authLogin('light', 'error'),
  'AuthSessaoExpirada.dc.html': authLogin('light', 'expired'),
  'AuthCadastro.dc.html': authSignup('light'),
  'AuthConfirmeEmail.dc.html': authConfirm('light'),
  'AuthEsqueciSenha.dc.html': authForgot('light'),
  'AuthRedefinirSenha.dc.html': authReset('light'),
  'AuthLoginDark.dc.html': authLogin('dark'),
  'Tokens.dc.html': tokensBoard(),
  'Componentes.dc.html': componentes('light'),
};
for (const [n, c] of Object.entries(files)) writeFileSync(n, c);

const G = 60;
const ab = (file, x, y, w, h, page, title) => ({ file, x, y, w, h, page, ...(title ? { title } : {}) });
const canvas = {
  pages: [{ id: 'fluxos', name: 'Fluxos e telas' }, { id: 'sistema', name: 'Sistema (tokens e componentes)' }],
  artboards: [
    // row 0: auth
    ab('AuthLogin.dc.html', 0, 0, 480, 640, 'fluxos', 'Auth · Login'),
    ab('AuthLoginErro.dc.html', 540, 0, 480, 640, 'fluxos', 'Auth · Login (erro genérico)'),
    ab('AuthCadastro.dc.html', 1080, 0, 480, 640, 'fluxos', 'Auth · Cadastro'),
    ab('AuthConfirmeEmail.dc.html', 1620, 0, 480, 640, 'fluxos', 'Auth · Verifique seu e-mail'),
    ab('AuthEsqueciSenha.dc.html', 2160, 0, 480, 560, 'fluxos', 'Auth · Esqueci a senha'),
    ab('AuthRedefinirSenha.dc.html', 2700, 0, 480, 560, 'fluxos', 'Auth · Redefinir senha'),
    ab('AuthSessaoExpirada.dc.html', 3240, 0, 480, 640, 'fluxos', 'Auth · Sessão expirada'),
    ab('AuthLoginDark.dc.html', 3780, 0, 480, 640, 'fluxos', 'Auth · Login (dark)'),
    // row 1: dashboard
    ab('Main.dc.html', 0, 760, 1440, 960, 'fluxos', 'Dashboard · desktop light'),
    ab('DashboardDark.dc.html', 1500, 760, 1440, 960, 'fluxos', 'Dashboard · desktop dark'),
    ab('DashboardMobile.dc.html', 3000, 760, 390, 844, 'fluxos', 'Dashboard · mobile'),
    ab('DashboardMobileDark.dc.html', 3450, 760, 390, 844, 'fluxos', 'Dashboard · mobile dark'),
    ab('IndicadoresDrawerMobile.dc.html', 3900, 760, 390, 844, 'fluxos', 'Indicadores · drawer mobile'),
    // row 2
    ab('DashboardSeletor.dc.html', 0, 1840, 1440, 960, 'fluxos', 'Dashboard · seletor de ativo aberto'),
    ab('DashboardOnboarding.dc.html', 1500, 1840, 1440, 960, 'fluxos', 'Dashboard · primeiro acesso'),
    ab('MercadoMobile.dc.html', 3000, 1840, 390, 844, 'fluxos', 'Mercado · mobile'),
    // row 3
    ab('Mercado.dc.html', 0, 2920, 1440, 900, 'fluxos', 'Mercado · tabela 24h'),
    ab('MercadoDark.dc.html', 1500, 2920, 1440, 900, 'fluxos', 'Mercado · dark'),
    // row 4
    ab('Estados.dc.html', 0, 3940, 1440, 900, 'fluxos', 'Estados · loading / vazio / erro / warm-up / stale / sessão'),
    ab('EstadosDark.dc.html', 1500, 3940, 1440, 900, 'fluxos', 'Estados · dark'),
    ab('PrevisoesReserva.dc.html', 3000, 3940, 960, 520, 'fluxos', 'Previsões · reserva (marco 3)'),
    // sistema
    ab('Tokens.dc.html', 0, 0, 1400, 980, 'sistema', 'Tokens · cor, séries, tipografia'),
    ab('Componentes.dc.html', 1460, 0, 1440, 1040, 'sistema', 'Inventário de componentes (Nuxt UI)'),
  ],
  annotations: [
    { id: 'nota-auth', x: 0, y: -130, w: 520, text: 'Fluxo de auth (Supabase e-mail+senha). Mensagens genéricas: login falho = "E-mail ou senha inválidos."; cadastro/esqueci = "Se este e-mail for novo/existir…". Sessão expirada volta ao login com aviso discreto e preserva ?symbol&tf.', page: 'fluxos' },
    { id: 'nota-dash', x: 0, y: 640, w: 640, text: 'Assinatura visual: o SELO DE SNAPSHOT (toolbar) + a LINHA DE CORTE no último candle. Nada é tempo real; a UI diz quando o dado termina. À direita da linha, área hachurada reservada para a previsão (marco 3).', page: 'fluxos' },
    { id: 'nota-mercado', x: 0, y: 2840, w: 520, text: 'Decisão do usuário: tabela 24h em rota própria /mercado (não no dashboard). O dashboard mantém só o Resumo 24h do ativo selecionado (faixa de stat tiles).', page: 'fluxos' },
    { id: 'nota-sistema', x: 0, y: -110, w: 560, text: 'Paleta de séries validada com dataviz/validate_palette.js (light/dark). Velas light: deutan ΔE 6.1 → codificação secundária obrigatória (▲▼, sinal, opção de alta vazada).', page: 'sistema' },
  ],
  launch: { view: 'canvas', page: 'fluxos' },
};
writeFileSync('canvas.json', JSON.stringify(canvas, null, 2));
console.log('ok', Object.keys(files).length, 'artboards');
