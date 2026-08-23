// Gera os artboards .dc.html do canvas de design v2 — Dark-Tech (crypto-forecasting-app)
// Decisões: dark-only · Google Sans / Google Sans Code · alta = vidro branco-gelo vazado · baixa = vermelho
// Cores proibidas: roxo, rosa, verde, laranja, gradientes multicoloridos.
import { writeFileSync } from 'node:fs';

// ---------- tokens (Dark-Tech) ----------
const T = {
  bg: '#060b16', bgDeep: '#04070f',
  glass: 'linear-gradient(160deg, rgba(30,48,80,.42), rgba(12,22,42,.55))',
  glassHi: 'linear-gradient(160deg, rgba(40,64,104,.5), rgba(14,26,50,.6))',
  solid: '#0c1626', solid2: '#101c30',
  muted: 'rgba(216,230,245,.05)', accented: 'rgba(216,230,245,.09)',
  border: 'rgba(216,230,245,.14)', borderMuted: 'rgba(216,230,245,.08)', borderStrong: 'rgba(216,230,245,.26)',
  textHi: '#f6f9fd', text: '#dde6f2', textMuted: '#9fb0c7', textDim: '#66788f',
  electric: '#3e86f7', electricSoft: 'rgba(62,134,247,.16)', electricGlow: '0 0 24px rgba(62,134,247,.35)',
  cyan: '#5fc4ff', cyanSoft: 'rgba(95,196,255,.12)',                       // 3ª cor (glow da logo) — reservada a IA/previsão
  ice: '#dbe7f5', iceSoft: 'rgba(219,231,245,.10)',
  up: '#dbe7f5', down: '#e5484d',
  warn: '#d6b25e', warnBg: 'rgba(214,178,94,.10)', danger: '#e5484d', dangerBg: 'rgba(229,72,77,.10)',
  sma20: '#4f8ff7', sma50: '#2596be', sma200: '#c8d9ef', ema12: '#8ab8ff', ema26: '#2f5fd0',
  bb: 'rgba(200,217,239,.55)', bbFill: 'rgba(200,217,239,.05)', rsi: '#4f8ff7',
  upA: 'rgba(219,231,245,.28)', downA: 'rgba(229,72,77,.30)',
  shadow: '0 12px 40px rgba(0,0,0,.5)',
};
const FONTS = `<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Google+Sans:wght@400;500;700&amp;family=Google+Sans+Code:wght@400;500&amp;display=swap">`;
const SANS = `'Google Sans', 'Segoe UI', system-ui, sans-serif`;
const MONO = `'Google Sans Code', ui-monospace, Consolas, monospace`;

function baseCss(t) {
  return `
  body { margin:0; background:${t.bg}; color:${t.text}; font-family:${SANS}; font-size:13.5px; line-height:1.5; -webkit-font-smoothing:antialiased; }
  a { color:${t.electric}; text-decoration:none; } a:hover { color:${t.cyan}; text-decoration:underline; }
  * { box-sizing:border-box; }
  .mono { font-family:${MONO}; font-variant-numeric:tabular-nums; }
  .eyebrow { font-family:${MONO}; font-size:11px; font-weight:500; letter-spacing:.08em; text-transform:uppercase; color:${t.textMuted}; }
  .glass { background:${t.glass}; border:1px solid ${t.border}; border-radius:12px; box-shadow:inset 0 1px 0 rgba(255,255,255,.07); }
  .glass-hi { background:${t.glassHi}; border:1px solid ${t.borderStrong}; border-radius:12px; box-shadow:inset 0 1px 0 rgba(255,255,255,.10), ${t.electricGlow}; }
  .btn { display:inline-flex; align-items:center; justify-content:center; gap:7px; height:34px; padding:0 14px; border-radius:8px; border:1px solid ${t.border}; background:rgba(216,230,245,.04); color:${t.text}; font:500 13.5px ${SANS}; cursor:pointer; white-space:nowrap; }
  .btn.primary { background:${t.electric}; border-color:${t.electric}; color:#04070f; box-shadow:${t.electricGlow}; font-weight:700; }
  .btn.ghost { border-color:transparent; background:transparent; color:${t.textMuted}; }
  .btn.lg { height:40px; font-size:14px; }
  .btn.block { width:100%; }
  .input { display:flex; align-items:center; gap:9px; height:40px; padding:0 12px; border:1px solid ${t.border}; border-radius:8px; background:rgba(4,8,18,.5); color:${t.text}; font:400 14px ${SANS}; }
  .input .ph { color:${t.textDim}; }
  .label { display:block; font-size:13px; font-weight:500; color:${t.text}; margin-bottom:6px; }
  .hint { font-size:12px; color:${t.textMuted}; }
  .chip { display:inline-flex; align-items:center; gap:6px; height:24px; padding:0 9px; border-radius:999px; border:1px solid ${t.border}; background:rgba(216,230,245,.04); font-size:11.5px; color:${t.textMuted}; }
  .chip.ai { border-color:rgba(95,196,255,.4); background:${t.cyanSoft}; color:${t.cyan}; }
  .focus { outline:2px solid ${t.electric}; outline-offset:2px; }
  .up { color:${t.ice}; } .down { color:${t.down}; }
  .tbl { width:100%; border-collapse:collapse; }
  .tbl th { text-align:right; font-family:${MONO}; font-size:11px; font-weight:500; letter-spacing:.08em; text-transform:uppercase; color:${t.textMuted}; padding:11px 12px; border-bottom:1px solid ${t.border}; white-space:nowrap; }
  .tbl td { text-align:right; padding:11px 12px; border-bottom:1px solid ${t.borderMuted}; font-family:${MONO}; font-variant-numeric:tabular-nums; font-size:13px; color:${t.text}; white-space:nowrap; }
  .tbl th:first-child, .tbl td:first-child { text-align:left; }
  .tbl tr.sel td { background:${t.electricSoft}; }
  .tbl tr.hover td { background:${t.muted}; }
  .sk { background:linear-gradient(90deg, rgba(216,230,245,.05) 25%, rgba(216,230,245,.10) 50%, rgba(216,230,245,.05) 75%); border-radius:4px; }
  .logoimg { mix-blend-mode:screen; }
  `;
}

// ---------- icons (stroke) ----------
const I = (d, s = 16) => `<svg width="${s}" height="${s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${d}</svg>`;
const ic = {
  search: s => I('<circle cx="11" cy="11" r="7"></circle><path d="m20 20-3.5-3.5"></path>', s),
  chevron: s => I('<path d="m6 9 6 6 6-6"></path>', s),
  refresh: s => I('<path d="M21 12a9 9 0 1 1-3-6.7"></path><path d="M21 3v6h-6"></path>', s),
  user: s => I('<circle cx="12" cy="8" r="4"></circle><path d="M4 21a8 8 0 0 1 16 0"></path>', s),
  check: s => I('<path d="m5 12 5 5L20 7"></path>', s),
  alert: s => I('<path d="M12 9v4M12 17h.01"></path><path d="M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z"></path>', s),
  xcircle: s => I('<circle cx="12" cy="12" r="9"></circle><path d="m15 9-6 6M9 9l6 6"></path>', s),
  info: s => I('<circle cx="12" cy="12" r="9"></circle><path d="M12 16v-4M12 8h.01"></path>', s),
  eye: s => I('<path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12z"></path><circle cx="12" cy="12" r="3"></circle>', s),
  back: s => I('<path d="m12 19-7-7 7-7M19 12H5"></path>', s),
  fwd: s => I('<path d="m12 5 7 7-7 7M5 12h14"></path>', s),
  mail: s => I('<rect x="3" y="5" width="18" height="14" rx="2"></rect><path d="m3 7 9 6 9-6"></path>', s),
  clock: s => I('<circle cx="12" cy="12" r="9"></circle><path d="M12 7v5l3 2"></path>', s),
  layers: s => I('<path d="m12 2 9 5-9 5-9-5 9-5z"></path><path d="m3 12 9 5 9-5M3 17l9 5 9-5"></path>', s),
  table: s => I('<rect x="3" y="4" width="18" height="16" rx="2"></rect><path d="M3 10h18M9 4v16"></path>', s),
  candle: s => I('<path d="M7 5v3M7 16v3M17 3v3M17 14v4"></path><rect x="5" y="8" width="4" height="8" rx="1"></rect><rect x="15" y="6" width="4" height="8" rx="1"></rect>', s),
  home: s => I('<path d="m3 10 9-7 9 7v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path><path d="M9 21v-8h6v8"></path>', s),
  x: s => I('<path d="M18 6 6 18M6 6l12 12"></path>', s),
  sliders: s => I('<path d="M4 21v-7M4 10V3M12 21v-9M12 8V3M20 21v-5M20 12V3M1 14h6M9 8h6M17 16h6"></path>', s),
  sort: s => I('<path d="m7 15 5 5 5-5M7 9l5-5 5 5"></path>', s),
  lock: s => I('<rect x="4" y="11" width="16" height="10" rx="2"></rect><path d="M8 11V7a4 4 0 0 1 8 0v4"></path>', s),
  inbox: s => I('<path d="M22 12h-6l-2 3h-4l-2-3H2"></path><path d="M5.5 5.1 2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.5-6.9A2 2 0 0 0 16.8 4H7.2a2 2 0 0 0-1.7 1.1z"></path>', s),
  sparkle: s => I('<path d="M12 3v4M12 17v4M3 12h4M17 12h4M5.6 5.6l2.8 2.8M15.6 15.6l2.8 2.8M5.6 18.4l2.8-2.8M15.6 8.4l2.8-2.8"></path>', s),
  bell: s => I('<path d="M18 8a6 6 0 0 0-12 0c0 7-3 9-3 9h18s-3-2-3-9"></path><path d="M13.7 21a2 2 0 0 1-3.4 0"></path>', s),
  phone: s => I('<rect x="7" y="2" width="10" height="20" rx="2"></rect><path d="M11 18h2"></path>', s),
  wave: s => I('<path d="M2 12h3l2-7 4 14 3-10 2 5 2-2h4"></path>', s),
  gap: s => I('<path d="M3 6h18M3 18h18"></path><path d="m9 12 3-3 3 3M9 12h6"></path>', s),
  volume: s => I('<path d="M4 20V10M10 20V4M16 20v-9M22 20H2"></path>', s),
  github: s => I('<path d="M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.4 5.4 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65S8.93 17.38 9 18v4"></path><path d="M9 18c-4.51 2-5-2-7-2"></path>', s),
  linkedin: s => I('<path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-4 0v7h-4v-7a6 6 0 0 1 6-6z"></path><rect x="2" y="9" width="4" height="12"></rect><circle cx="4" cy="4" r="2"></circle>', s),
};

// ---------- dados sintéticos ----------
function rng(seed) { let s = seed >>> 0; return () => { s = (s * 1664525 + 1013904223) >>> 0; return s / 4294967296; }; }
function genCandles(n, seed = 7, base = 113000) {
  const r = rng(seed); const out = []; let c = base;
  for (let i = 0; i < n; i++) {
    const drift = Math.sin(i / 11) * 180 + (r() - 0.48) * 900;
    const o = c; c = Math.max(base * 0.8, o + drift);
    const hi = Math.max(o, c) + r() * 500; const lo = Math.min(o, c) - r() * 500;
    out.push({ o, h: hi, l: lo, c, v: 600 + r() * 1400 + (Math.abs(drift) > 400 ? 900 : 0) });
  }
  return out;
}
const sma = (a, p) => a.map((_, i) => i + 1 < p ? null : a.slice(i + 1 - p, i + 1).reduce((x, y) => x + y, 0) / p);
function ema(a, p) { const k = 2 / (p + 1); let e = null; return a.map((v, i) => { if (i + 1 < p) return null; if (e === null) { e = a.slice(0, p).reduce((x, y) => x + y, 0) / p; return e; } e = v * k + e * (1 - k); return e; }); }
function rsiF(a, p = 14) { return a.map((_, i) => { if (i < p) return null; let g = 0, l = 0; for (let j = i - p + 1; j <= i; j++) { const d = a[j] - a[j - 1]; if (d > 0) g += d; else l -= d; } if (l === 0) return 100; return 100 - 100 / (1 + (g / p) / (l / p)); }); }

// ---------- gráfico SVG ----------
function chartSvg(t, W, H, o = {}) {
  const { total = 130, show = 92, crossAt = 0.62, cut = true, forecast = true, panes = ['rsi', 'macd'], overlays = ['sma20', 'sma50'], skeleton = false, mobile = false, seed = 7, padTop = mobile ? 82 : 56 } = o;
  const data = genCandles(total, seed); const closes = data.map(d => d.c);
  const S = { sma20: sma(closes, 20), sma50: sma(closes, 50), sma200: sma(closes, 200), ema12: ema(closes, 12), ema26: ema(closes, 26) };
  const bbm = sma(closes, 20); const bbu = bbm.map(m => m == null ? null : m + 900), bbl = bbm.map(m => m == null ? null : m - 900);
  const R = rsiF(closes); const mac = closes.map((_, i) => S.ema12[i] == null || S.ema26[i] == null ? null : S.ema12[i] - S.ema26[i]);
  const macSig = ema(mac.map(v => v ?? 0), 9).map((v, i) => mac[i] == null || i < 34 ? null : v);
  const first = total - show; const vis = data.slice(first);
  const axW = mobile ? 62 : 66; const padL = 8; const fcW = forecast ? Math.round((W - axW) * (mobile ? 0.16 : 0.13)) : 0;
  const plotW = W - axW - padL - fcW; const step = plotW / show; const cw = Math.max(2, Math.floor(step * 0.62));
  const x = i => padL + i * step + step / 2;
  const priceH = panes.length ? Math.round(H * (panes.length === 2 ? 0.56 : 0.72)) : H;
  const paneH = panes.length ? Math.round((H - priceH) / panes.length) : 0;
  const hi = Math.max(...vis.map(d => d.h)) * 1.004, lo = Math.min(...vis.map(d => d.l)) * 0.996;
  const py = v => padTop + (priceH - padTop - priceH * 0.22) * (1 - (v - lo) / (hi - lo));
  const volMax = Math.max(...vis.map(d => d.v)); const volBase = priceH - 4; const volH = priceH * 0.18;
  let s = `<svg width="${W}" height="${H}" viewBox="0 0 ${W} ${H}" font-family="${MONO}" font-size="11" style="display:block">`;
  const ticks = 5; for (let k = 0; k <= ticks; k++) { const v = lo + (hi - lo) * k / ticks; const y = py(v); s += `<line x1="0" x2="${W - axW}" y1="${y.toFixed(1)}" y2="${y.toFixed(1)}" stroke="${t.borderMuted}"></line><text x="${W - axW + 8}" y="${(y + 4).toFixed(1)}" fill="${t.textDim}">${Math.round(v).toLocaleString('pt-BR')}</text>`; }
  if (skeleton) { s += `<rect x="${padL}" y="${padTop - 12}" width="${plotW}" height="${priceH - padTop - 8}" rx="6" fill="${t.muted}"></rect>`; panes.forEach((p, pi) => { const top = priceH + pi * paneH; s += `<rect x="${padL}" y="${top + 14}" width="${plotW}" height="${paneH - 28}" rx="6" fill="${t.muted}"></rect>`; }); return s + '</svg>'; }
  panes.forEach((p, pi) => { const top = priceH + pi * paneH; s += `<line x1="0" x2="${W}" y1="${top}" y2="${top}" stroke="${t.border}"></line>`; });
  if (overlays.includes('bb')) { let up = ''; const pts = []; vis.forEach((d, i) => { const gi = first + i; if (bbu[gi] == null) return; up += `${up ? 'L' : 'M'}${x(i).toFixed(1)},${py(bbu[gi]).toFixed(1)} `; pts.push([x(i), py(bbl[gi])]); }); if (up) { const lowRev = pts.slice().reverse().map(p => `L${p[0].toFixed(1)},${p[1].toFixed(1)}`).join(' '); s += `<path d="${up}${lowRev}Z" fill="${t.bbFill}"></path><path d="${up}" fill="none" stroke="${t.bb}" stroke-dasharray="2 3"></path><path d="M${pts.map(p => `${p[0].toFixed(1)},${p[1].toFixed(1)}`).join(' L')}" fill="none" stroke="${t.bb}" stroke-dasharray="2 3"></path>`; } }
  vis.forEach((d, i) => { const h = volH * d.v / volMax; s += `<rect x="${(x(i) - cw / 2).toFixed(1)}" y="${(volBase - h).toFixed(1)}" width="${cw}" height="${h.toFixed(1)}" fill="${d.c >= d.o ? t.upA : t.downA}"></rect>`; });
  // velas: alta = vazada (vidro gelo), baixa = preenchida vermelha
  vis.forEach((d, i) => { const upc = d.c >= d.o; const col = upc ? t.ice : t.down; const y1 = py(Math.max(d.o, d.c)), y2 = py(Math.min(d.o, d.c)); const bh = Math.max(1.5, y2 - y1); s += `<line x1="${x(i).toFixed(1)}" x2="${x(i).toFixed(1)}" y1="${py(d.h).toFixed(1)}" y2="${py(d.l).toFixed(1)}" stroke="${col}" stroke-width="1"></line>`; s += upc ? `<rect x="${(x(i) - cw / 2).toFixed(1)}" y="${y1.toFixed(1)}" width="${cw}" height="${bh.toFixed(1)}" fill="rgba(219,231,245,.10)" stroke="${t.ice}" stroke-width="1"></rect>` : `<rect x="${(x(i) - cw / 2).toFixed(1)}" y="${y1.toFixed(1)}" width="${cw}" height="${bh.toFixed(1)}" fill="${col}"></rect>`; });
  const styleOf = { sma20: [t.sma20, 1.2, ''], sma50: [t.sma50, 1.8, ''], sma200: [t.sma200, 2.2, ''], ema12: [t.ema12, 1.2, '4 3'], ema26: [t.ema26, 1.8, '4 3'] };
  overlays.filter(k => styleOf[k]).forEach(k => { let d = '', pen = false; vis.forEach((_, i) => { const v = S[k][first + i]; if (v == null) { pen = false; return; } d += `${pen ? 'L' : 'M'}${x(i).toFixed(1)},${py(v).toFixed(1)} `; pen = true; }); const [c, w, da] = styleOf[k]; s += `<path d="${d}" fill="none" stroke="${c}" stroke-width="${w}" ${da ? `stroke-dasharray="${da}"` : ''}></path>`; });
  panes.forEach((p, pi) => {
    const top = priceH + pi * paneH; const ph = paneH;
    if (p === 'rsi') {
      const ry = v => top + 14 + (ph - 28) * (1 - v / 100);
      s += `<rect x="0" y="${ry(70).toFixed(1)}" width="${W - axW}" height="${(ry(30) - ry(70)).toFixed(1)}" fill="${t.electric}" opacity="0.05"></rect>`;
      [30, 70].forEach(v => s += `<line x1="0" x2="${W - axW}" y1="${ry(v).toFixed(1)}" y2="${ry(v).toFixed(1)}" stroke="${t.border}" stroke-dasharray="3 3"></line><text x="${W - axW + 8}" y="${(ry(v) + 4).toFixed(1)}" fill="${t.textDim}">${v}</text>`);
      let d = '', pen = false; vis.forEach((_, i) => { const v = R[first + i]; if (v == null) { pen = false; return; } d += `${pen ? 'L' : 'M'}${x(i).toFixed(1)},${ry(v).toFixed(1)} `; pen = true; }); s += `<path d="${d}" fill="none" stroke="${t.rsi}" stroke-width="1.5"></path>`;
      s += `<text x="${padL + 2}" y="${top + 16}" fill="${t.textMuted}" font-size="11">RSI 14 <tspan fill="${t.rsi}">${R[total - 1].toFixed(1).replace('.', ',')}</tspan></text>`;
    } else if (p === 'macd') {
      const vals = vis.map((_, i) => mac[first + i]).filter(v => v != null); const mx = Math.max(...vals.map(Math.abs)) * 1.1;
      const my = v => top + 14 + (ph - 28) * (1 - (v + mx) / (2 * mx));
      s += `<line x1="0" x2="${W - axW}" y1="${my(0).toFixed(1)}" y2="${my(0).toFixed(1)}" stroke="${t.border}"></line>`;
      vis.forEach((_, i) => { const gi = first + i; if (mac[gi] == null || macSig[gi] == null) return; const h = mac[gi] - macSig[gi]; const y0 = my(0), y1 = my(h); s += `<rect x="${(x(i) - cw / 2).toFixed(1)}" y="${Math.min(y0, y1).toFixed(1)}" width="${cw}" height="${Math.max(1, Math.abs(y1 - y0)).toFixed(1)}" fill="${h >= 0 ? t.ice : t.down}" opacity="0.45"></rect>`; });
      [[mac, t.sma20], [macSig, t.ice]].forEach(([arr, c]) => { let d = '', pen = false; vis.forEach((_, i) => { const v = arr[first + i]; if (v == null) { pen = false; return; } d += `${pen ? 'L' : 'M'}${x(i).toFixed(1)},${my(v).toFixed(1)} `; pen = true; }); s += `<path d="${d}" fill="none" stroke="${c}" stroke-width="1.5"></path>`; });
      s += `<text x="${padL + 2}" y="${top + 16}" fill="${t.textMuted}" font-size="11">MACD 12·26·9 <tspan fill="${t.sma20}">${mac[total - 1].toFixed(0).replace('-', '−')}</tspan> <tspan fill="${t.ice}">${macSig[total - 1].toFixed(0).replace('-', '−')}</tspan></text>`;
    }
  });
  const labels = mobile ? 4 : 7; for (let k = 0; k < labels; k++) { const i = Math.round(k * (show - 1) / (labels - 1)); const abs = i + 6; const day = 15 + Math.floor(abs / 24); const hr = abs % 24; const anchor = k === 0 ? 'start' : k === labels - 1 ? 'end' : 'middle'; s += `<text x="${(k === 0 ? padL : x(i)).toFixed(1)}" y="${H - 6}" fill="${t.textDim}" text-anchor="${anchor}">${hr < 4 || k === 0 ? `${day} ago` : `${String(hr).padStart(2, '0')}:00`}</text>`; }
  if (crossAt) { const ci = Math.round(show * crossAt); const cx = x(ci); s += `<line x1="${cx.toFixed(1)}" x2="${cx.toFixed(1)}" y1="0" y2="${H - 18}" stroke="${t.textDim}" stroke-dasharray="3 3"></line>`; const d = vis[ci]; const cy = py(d.c); s += `<line x1="0" x2="${W - axW}" y1="${cy.toFixed(1)}" y2="${cy.toFixed(1)}" stroke="${t.textDim}" stroke-dasharray="3 3"></line><rect x="${W - axW + 2}" y="${(cy - 9).toFixed(1)}" width="${axW - 4}" height="18" rx="4" fill="${t.ice}"></rect><text x="${W - axW + 8}" y="${(cy + 4).toFixed(1)}" fill="${t.bgDeep}">${Math.round(d.c).toLocaleString('pt-BR')}</text><rect x="${(cx - 42).toFixed(1)}" y="${H - 19}" width="84" height="17" rx="4" fill="${t.ice}"></rect><text x="${cx.toFixed(1)}" y="${H - 7}" fill="${t.bgDeep}" text-anchor="middle">18 ago 14:00</text>`; }
  if (cut) {
    const cx = x(show - 1) + step / 2 + 2; const endX = W - axW - 4;
    s += `<line x1="${cx.toFixed(1)}" x2="${cx.toFixed(1)}" y1="0" y2="${H - 18}" stroke="${t.cyan}" stroke-dasharray="2 3" opacity="0.9"></line>`;
    if (forecast) {
      const lc = vis[show - 1].c; const y0 = py(lc);
      const yBest = y0 - Math.min(64, priceH * 0.16), yExp = y0 - 10, yWorst = y0 + Math.min(70, priceH * 0.18);
      s += `<path d="M${cx},${y0.toFixed(1)} L${endX},${yBest.toFixed(1)} L${endX},${yWorst.toFixed(1)} Z" fill="${t.cyan}" opacity="0.08"></path>`;
      s += `<path d="M${cx},${y0.toFixed(1)} L${endX},${yBest.toFixed(1)}" stroke="${t.ice}" stroke-width="1" stroke-dasharray="2 3" opacity="0.85"></path>`;
      s += `<path d="M${cx},${y0.toFixed(1)} L${endX},${yExp.toFixed(1)}" stroke="${t.cyan}" stroke-width="1.6" stroke-dasharray="5 3"></path>`;
      s += `<path d="M${cx},${y0.toFixed(1)} L${endX},${yWorst.toFixed(1)}" stroke="${t.down}" stroke-width="1" stroke-dasharray="2 3" opacity="0.85"></path>`;
      if (!mobile) { s += `<text x="${(endX - 4).toFixed(1)}" y="${(yBest - 5).toFixed(1)}" fill="${t.ice}" text-anchor="end" font-size="10.5">melhor</text><text x="${(endX - 4).toFixed(1)}" y="${(yExp - 6).toFixed(1)}" fill="${t.cyan}" text-anchor="end" font-size="10.5">esperada</text><text x="${(endX - 4).toFixed(1)}" y="${(yWorst + 13).toFixed(1)}" fill="${t.down}" text-anchor="end" font-size="10.5">pior</text>`; }
    }
  }
  return s + '</svg>';
}

// ---------- blocos ----------
const logoImg = (sz = 28, alt = '') => `<img src="./logo.jpg" width="${sz}" height="${sz}" alt="${alt}" class="logoimg" style="border-radius:8px; object-fit:cover;">`;
const brand = (t, sz = 28, fs = 15) => `<span style="display:inline-flex; align-items:center; gap:10px">${logoImg(sz)}<span style="font-weight:700; font-size:${fs}px; color:${t.textHi}; letter-spacing:-.01em">crypto forecasting</span></span>`;

function legend(t, o = {}) {
  const { symbol = 'BTCUSDT', tf = '1h', rows = [], mobile = false, forecastChip = true } = o;
  const ohlc = `<span style="color:${t.textMuted}">A</span> <span class="mono">113.250,1</span> <span style="color:${t.textMuted}">M</span> <span class="mono">113.900,0</span> <span style="color:${t.textMuted}">m</span> <span class="mono">112.800,5</span> <span style="color:${t.textMuted}">F</span> <span class="mono" style="color:${t.ice}">113.512,3</span> <span style="color:${t.textMuted}">Vol</span> <span class="mono">1.284,5</span>`;
  return `<div style="position:absolute; left:14px; top:12px; display:flex; flex-direction:column; gap:4px; font-size:12px; pointer-events:none;">
    <div style="display:flex; align-items:center; gap:8px; flex-wrap:wrap;"><span translate="no" style="font-weight:700; color:${t.textHi}">${symbol}</span><span class="mono" style="color:${t.textMuted}">· ${tf} · <span style="color:${t.textDim}">18 ago 14:00 UTC</span></span>${mobile ? '' : `<span>${ohlc}</span>`}</div>
    ${mobile ? `<div style="font-size:11px">${ohlc}</div>` : ''}
    <div style="display:flex; gap:12px; flex-wrap:wrap; font-size:12px">${rows.map(([n, c, v, note]) => `<span style="display:inline-flex; align-items:center; gap:6px"><span style="width:12px; height:2px; background:${c}; display:inline-block"></span><span style="color:${t.textMuted}">${n}</span><span class="mono" style="color:${t.text}">${v}</span>${note ? `<span style="color:${t.textDim}; font-size:11px">${note}</span>` : ''}</span>`).join('')}${forecastChip ? `<span class="chip ai" style="height:20px; font-size:10.5px">${ic.sparkle(11)} previsão IA · modelo v0 · em validação</span>` : ''}</div>
  </div>`;
}

function stamp(t, o = {}) {
  const { state = 'fresh', mobile = false, label = 'Velas: 19 ago 00:00 UTC · há 6 h' } = o;
  const col = state === 'stale' ? t.warn : t.textMuted; const bg = state === 'stale' ? t.warnBg : 'rgba(216,230,245,.04)';
  const txt = state === 'stale' ? (mobile ? 'Velas: há 31 h' : 'Velas atualizadas em 18 ago 00:00 UTC · há 31 h') : (mobile ? 'Velas: 19 ago · há 6 h' : label);
  return `<span class="mono" title="Candles e indicadores atualizam 1x/dia (~00:05 UTC); resumo 24h de hora em hora. Nada é tempo real." style="display:inline-flex; align-items:center; gap:8px; height:34px; padding:0 11px; border:1px solid ${state === 'stale' ? t.warn : t.border}; border-radius:8px; background:${bg}; color:${col}; font-size:11px; letter-spacing:.02em; white-space:nowrap;">${state === 'stale' ? `<span style="color:${t.warn}; display:inline-flex">${ic.alert(14)}</span>` : `<span style="width:7px; height:7px; border-radius:999px; background:${t.cyan}; display:inline-block"></span>`}<span style="font-weight:500; text-transform:uppercase; letter-spacing:.08em">snapshot</span><span style="color:${t.border}">|</span><span>${txt}</span></span>`;
}

function header(t, o = {}) {
  const { active = 'home', mobile = false } = o;
  const nav = [['home', 'Início', ic.home(16)], ['graficos', 'Gráficos', ic.candle(16)], ['previsoes', 'Previsões', ic.sparkle(16)], ['mercado', 'Mercado', ic.table(16)]];
  if (mobile) return `<header style="display:flex; align-items:center; justify-content:space-between; height:54px; padding:0 14px; background:rgba(6,11,22,.85); border-bottom:1px solid ${t.border};">
    ${brand(t, 26, 14)}
    <button class="btn ghost" aria-label="Conta" style="width:38px; padding:0">${ic.user(18)}</button>
  </header>`;
  return `<header style="display:flex; align-items:center; justify-content:space-between; height:58px; padding:0 24px; background:rgba(6,11,22,.85); border-bottom:1px solid ${t.border};">
    <div style="display:flex; align-items:center; gap:28px">
      ${brand(t)}
      <nav style="display:flex; gap:4px" aria-label="Principal">${nav.map(([k, l, i]) => `<a href="#" aria-current="${k === active ? 'page' : 'false'}" style="display:inline-flex; align-items:center; gap:7px; height:34px; padding:0 12px; border-radius:8px; font-weight:500; color:${k === active ? t.textHi : t.textMuted}; background:${k === active ? t.electricSoft : 'transparent'}; ${k === active ? `border:1px solid rgba(62,134,247,.35);` : ''} text-decoration:none">${i}<span>${l}</span></a>`).join('')}</nav>
    </div>
    <div style="display:flex; align-items:center; gap:6px">
      <button class="btn ghost" style="gap:8px"><span style="width:26px; height:26px; border-radius:999px; background:${t.electricSoft}; color:${t.cyan}; display:inline-flex; align-items:center; justify-content:center; font:700 11px ${SANS}">GC</span><span>Gabriel</span>${ic.chevron(14)}</button>
    </div>
  </header>`;
}

function mobileTabs(t, active = 'home') {
  const items = [['home', 'Início', ic.home(20)], ['graficos', 'Gráficos', ic.candle(20)], ['previsoes', 'Previsões', ic.sparkle(20)], ['mercado', 'Mercado', ic.table(20)]];
  return `<div style="position:absolute; left:0; right:0; bottom:0; display:flex; justify-content:space-around; align-items:center; height:64px; padding-bottom:max(8px, env(safe-area-inset-bottom)); background:rgba(6,11,22,.92); border-top:1px solid ${t.border}">
    ${items.map(([k, l, i]) => `<a href="#" aria-current="${k === active ? 'page' : 'false'}" class="btn ghost" style="flex-direction:column; gap:2px; height:48px; min-width:68px; font-size:11px; color:${k === active ? t.cyan : t.textMuted}; text-decoration:none">${i}<span>${l}</span></a>`).join('')}
  </div>`;
}

function toolbar(t, o = {}) {
  const { tf = '1h', state = 'fresh', symbol = 'BTCUSDT' } = o;
  const tfs = ['15m', '1h', '1d'].map(k => `<button class="btn mono" aria-pressed="${k === tf}" style="height:30px; border:none; border-radius:6px; padding:0 12px; background:${k === tf ? t.electricSoft : 'transparent'}; color:${k === tf ? t.cyan : t.textMuted};">${k}</button>`).join('');
  return `<div style="display:flex; align-items:center; justify-content:space-between; gap:12px; padding:12px 24px; flex-wrap:wrap">
    <div style="display:flex; align-items:center; gap:10px">
      <button class="btn" aria-haspopup="listbox" style="min-width:230px; justify-content:space-between; padding-left:11px"><span style="display:inline-flex; gap:8px; align-items:center"><span style="color:${t.textDim}">${ic.search(14)}</span><span class="mono" translate="no" style="font-weight:500; color:${t.textHi}">${symbol}</span><span style="color:${t.textMuted}; font-weight:400">Bitcoin / Tether</span></span>${ic.chevron(14)}</button>
      <div role="radiogroup" aria-label="Timeframe" style="display:inline-flex; gap:2px; padding:2px; background:rgba(4,8,18,.5); border:1px solid ${t.border}; border-radius:8px">${tfs}</div>
      <span class="hint mono" style="color:${t.textDim}">1h · últimos 30 dias</span>
    </div>
    <div style="display:flex; align-items:center; gap:8px">${stamp(t, { state })}<button class="btn" aria-label="Atualizar dados">${ic.refresh(14)}<span>Atualizar</span></button></div>
  </div>`;
}

function togglesPanel(t, o = {}) {
  const { on = ['sma20', 'sma50', 'vol', 'rsi', 'macd', 'ia'], w = 268 } = o;
  const groups = [
    ['Sobre o preço', [['sma20', 'SMA 20', t.sma20, 'solid'], ['sma50', 'SMA 50', t.sma50, 'solid'], ['sma200', 'SMA 200', t.sma200, 'solid'], ['ema12', 'EMA 12', t.ema12, 'dash'], ['ema26', 'EMA 26', t.ema26, 'dash'], ['bb', 'Bollinger 20·2', t.bb, 'dot'], ['vol', 'Volume', t.textDim, 'bar']]],
    ['Painéis abaixo', [['rsi', 'RSI 14', t.rsi, 'solid'], ['macd', 'MACD 12·26·9', t.sma20, 'solid']]],
    ['Modelo', [['ia', 'Previsão IA (cenários)', t.cyan, 'dash']]],
  ];
  const sw = (c, st) => st === 'bar' ? `<span style="display:inline-flex; gap:1px; align-items:flex-end; height:10px"><i style="width:3px; height:6px; background:${c}; display:block"></i><i style="width:3px; height:10px; background:${c}; display:block"></i><i style="width:3px; height:4px; background:${c}; display:block"></i></span>` : `<span style="width:16px; height:0; border-top:2px ${st === 'solid' ? 'solid' : st === 'dash' ? 'dashed' : 'dotted'} ${c}; display:inline-block"></span>`;
  return `<aside class="glass" aria-label="Indicadores" style="width:${w}px; flex:none; display:flex; flex-direction:column; overflow:hidden">
    <div style="display:flex; align-items:center; justify-content:space-between; padding:11px 14px 9px; border-bottom:1px solid ${t.border}"><span style="font-weight:700; color:${t.textHi}">Indicadores</span><span class="hint">salvos no navegador</span></div>
    ${groups.map(([g, items]) => `<div style="padding:8px 8px 4px"><div class="eyebrow" style="padding:4px 6px 6px">${g}</div>${items.map(([k, l, c, st]) => { const isOn = on.includes(k); return `<label style="display:flex; align-items:center; gap:10px; height:32px; padding:0 6px; border-radius:8px; cursor:pointer;"><span role="checkbox" tabindex="0" aria-checked="${isOn}" style="width:16px; height:16px; border-radius:4px; border:1px solid ${isOn ? t.electric : t.border}; background:${isOn ? t.electric : 'transparent'}; color:#04070f; display:inline-flex; align-items:center; justify-content:center">${isOn ? ic.check(12) : ''}</span>${sw(c, st)}<span style="flex:1; color:${isOn ? t.text : t.textMuted}">${l}</span>${k === 'sma200' ? `<span class="hint mono" title="Warm-up: SMA 200 só existe a partir da 200ª vela" style="font-size:10px">warm-up</span>` : ''}${k === 'ia' ? `<span class="chip ai" style="height:18px; font-size:9.5px; padding:0 6px">v0</span>` : ''}</label>`; }).join('')}</div>`).join('')}
    <div style="margin-top:auto; padding:10px 14px; border-top:1px solid ${t.border}; display:flex; flex-direction:column; gap:8px">
      <div class="hint" style="display:flex; gap:6px; align-items:flex-start"><span style="color:${t.textDim}; flex:none; margin-top:1px">${ic.info(14)}</span><span>Linhas começam só depois da janela de cálculo (warm-up). Não é erro.</span></div>
      <div style="display:flex; gap:6px"><button class="btn ghost" style="height:28px; font-size:12px; padding:0 8px">Restaurar padrão</button><button class="btn ghost" style="height:28px; font-size:12px; padding:0 8px">Limpar tudo</button></div>
    </div>
  </aside>`;
}

function kpiStrip(t, o = {}) {
  const { mobile = false } = o;
  const items = [['Último preço', '113.512,3', 'USDT'], ['Variação 24h', '▲ +2.048,9 · +1,84 %', '', 'up'], ['Previsão diária (IA)', '114.890', '+1,21 % vs real', 'ai'], ['Máx / Mín 24h', '114.120,0 · 110.902,1', ''], ['Bid / Ask', '113.510,0 / 113.512,9', 'spread 0,003 %'], ['Volume 24h', '38.412 BTC', '4,33 bi USDT · 4,21 mi trades']];
  return `<section aria-label="Resumo 24h" class="glass" style="display:flex; flex-direction:column">
    <div style="display:flex; align-items:center; justify-content:space-between; padding:9px 14px 7px; border-bottom:1px solid ${t.borderMuted}"><span class="eyebrow">Resumo 24h · <span translate="no">BTCUSDT</span></span><span class="hint mono" style="font-size:11px">${mobile ? '14:00 UTC · há 12 min' : 'snapshot 19 ago 14:00 UTC · há 12 min · atualiza de hora em hora'}</span></div>
    <div style="display:${mobile ? 'grid' : 'flex'}; ${mobile ? 'grid-template-columns:repeat(2, minmax(0,1fr));' : ''}">
    ${items.map(([l, v, s2, cls], i) => `<div style="display:flex; flex-direction:column; gap:2px; padding:10px ${mobile ? 12 : 14}px; ${mobile ? 'min-width:0;' : 'flex:1;'} ${i < items.length - 1 && !mobile ? `border-right:1px solid ${t.borderMuted}` : ''} ${mobile && i % 2 === 0 ? `border-right:1px solid ${t.borderMuted}` : ''} ${mobile && i < items.length - 2 ? `border-bottom:1px solid ${t.borderMuted}` : ''}"><span class="hint" style="font-size:11px; white-space:nowrap">${l}${cls === 'ai' ? ` <span style="color:${t.cyan}">${ic.sparkle(10)}</span>` : ''}</span><span class="mono" style="font-size:${mobile ? 12.5 : 14}px; font-weight:500; white-space:nowrap; color:${cls === 'up' ? t.ice : cls === 'ai' ? t.cyan : t.textHi}">${v}</span>${s2 ? `<span class="hint mono" style="font-size:11px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis">${s2}</span>` : ''}</div>`).join('')}
    </div>
  </section>`;
}

function wrap(t, title, body, { w, h }) {
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
<div aria-label="${title}" style="width:${w}px; height:${h}px; background:radial-gradient(1200px 600px at 70% -10%, rgba(62,134,247,.10), transparent 60%), ${t.bg}; color:${t.text}; font-family:${SANS}; overflow:hidden; display:flex; flex-direction:column; position:relative;">
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

// ---------- Tela 1: Login split ----------
const field = (t, label, ph, { type = 'text', icon = null, err = '', right = '' } = {}) => { const id = 'f-' + label.toLowerCase().replace(/[^a-z]+/g, '-'); return `<div><div style="display:flex; justify-content:space-between; align-items:baseline"><label class="label" for="${id}">${label}</label>${right}</div><div class="input" id="${id}" role="textbox" tabindex="0" style="${err ? `border-color:${t.danger}` : ''}">${icon ? `<span style="color:${t.textDim}">${icon}</span>` : ''}<span class="${ph.startsWith('•') || ph.includes('@') || ph.includes('+55') || ph.includes('Castro') ? '' : 'ph'}" style="flex:1">${ph}</span>${type === 'password' ? `<button type="button" aria-label="Mostrar senha" aria-pressed="false" style="display:inline-flex; align-items:center; justify-content:center; width:28px; height:28px; margin-right:-6px; border:none; background:transparent; color:${t.textDim}; cursor:pointer; border-radius:4px">${ic.eye(16)}</button>` : ''}</div>${err ? `<p style="margin:6px 0 0; font-size:12px; color:${t.danger}; display:flex; gap:6px; align-items:center">${ic.alert(14)}${err}</p>` : ''}</div>`; };

function loginSplit(variant = 'default') {
  const t = T; const W = 1440, H = 900;
  const expired = variant === 'expired'; const errored = variant === 'error';
  const bullets = [
    ['Snapshots diários, não ruído', 'Coletamos os top 20 pares USDT da Binance uma vez por dia e calculamos os indicadores por você.'],
    ['Previsões com contexto', 'Modelos de ML projetam os cenários de melhor caso, esperado e pior caso sobre o gráfico real.'],
    ['Alertas do que importa', 'Volatilidade, volume e o gap entre preço real e projeção, no seu primeiro acesso do dia.'],
  ];
  const body = `
  <div style="display:flex; flex:1; min-height:0">
    <section style="flex:1.1; position:relative; display:flex; flex-direction:column; padding:36px 56px; background:radial-gradient(900px 500px at 30% 20%, rgba(62,134,247,.14), transparent 60%), ${t.bgDeep}; border-right:1px solid ${t.border}">
      ${brand(t, 34, 17)}
      <div style="flex:1; display:flex; flex-direction:column; justify-content:center; gap:24px; max-width:540px">
        <img src="./logo.jpg" width="170" height="170" alt="Logo: velas de vidro com seta de alta em azul elétrico" class="logoimg" style="border-radius:24px; margin-left:-8px">
        <div>
          <h1 style="margin:0; text-wrap:balance; font-size:31px; line-height:1.2; font-weight:700; letter-spacing:-.02em; color:${t.textHi}">Enxergue o mercado um dia à frente.</h1>
          <p style="margin:10px 0 0; font-size:15px; color:${t.textMuted}; max-width:46ch">Forecasting de criptomoedas com dados reais da Binance, indicadores técnicos e previsões de IA.</p>
        </div>
        <ul style="list-style:none; margin:0; padding:0; display:flex; flex-direction:column; gap:13px">
          ${bullets.map(([h, p]) => `<li style="display:flex; gap:12px; align-items:flex-start"><span style="flex:none; width:30px; height:30px; border-radius:8px; background:${t.electricSoft}; border:1px solid rgba(62,134,247,.3); color:${t.cyan}; display:inline-flex; align-items:center; justify-content:center">${ic.check(15)}</span><span><span style="display:block; font-weight:500; color:${t.textHi}">${h}</span><span class="hint" style="font-size:12.5px">${p}</span></span></li>`).join('')}
        </ul>
      </div>
      <footer style="display:flex; align-items:center; justify-content:space-between; gap:12px">
        <span class="hint">Projeto desenvolvido por Gabriel Castro</span>
        <span style="display:inline-flex; gap:8px">
          <a href="https://github.com/gabriel-castro-dev" aria-label="GitHub de Gabriel Castro" style="display:inline-flex; align-items:center; justify-content:center; width:34px; height:34px; border:1px solid ${t.border}; border-radius:8px; color:${t.textMuted}">${ic.github(16)}</a>
          <a href="https://www.linkedin.com/" aria-label="LinkedIn de Gabriel Castro" style="display:inline-flex; align-items:center; justify-content:center; width:34px; height:34px; border:1px solid ${t.border}; border-radius:8px; color:${t.textMuted}">${ic.linkedin(16)}</a>
        </span>
      </footer>
    </section>
    <section style="flex:1; display:flex; flex-direction:column; align-items:center; justify-content:center; padding:40px; gap:16px">
      ${expired ? `<div role="status" class="glass" style="width:100%; max-width:400px; display:flex; gap:10px; align-items:flex-start; padding:11px 13px; color:${t.textMuted}; font-size:13px"><span style="color:${t.textDim}; flex:none; margin-top:1px">${ic.clock(16)}</span><span>Sua sessão expirou. Entre de novo para continuar. Você voltará para onde estava.</span></div>` : ''}
      <div class="glass" style="width:100%; max-width:400px; padding:30px 30px 26px; display:flex; flex-direction:column; gap:16px; backdrop-filter:blur(14px)">
        <div><h2 style="margin:0; text-wrap:balance; font-size:22px; font-weight:700; letter-spacing:-.01em; color:${t.textHi}">Entrar</h2><p class="hint" style="margin:4px 0 0">Use o e-mail e a senha da sua conta.</p></div>
        ${errored ? `<div role="alert" style="display:flex; gap:8px; align-items:flex-start; padding:10px 12px; border-radius:8px; background:${t.dangerBg}; border:1px solid rgba(229,72,77,.35); color:${t.danger}; font-size:13px"><span style="flex:none; margin-top:1px">${ic.xcircle(16)}</span><span>E-mail ou senha inválidos.</span></div>` : ''}
        ${field(t, 'E-mail', 'gabriel@exemplo.com', { icon: ic.mail(16) })}
        ${field(t, 'Senha', '••••••••••', { type: 'password', icon: ic.lock(16), right: `<a href="#" style="font-size:12px">Esqueci a senha</a>` })}
        <button class="btn primary lg block">Entrar</button>
        <p class="hint" style="margin:0; text-align:center">Não tem conta? <a href="#">Criar conta</a></p>
      </div>
      <p class="hint mono" style="margin:0; font-size:11px">Dados da Binance · snapshots diários · horários em UTC</p>
    </section>
  </div>`;
  return wrap(t, 'Login', body, { w: W, h: H });
}

function authCentered(title, inner, h = 640) {
  const t = T;
  const body = `
  <div style="display:flex; flex-direction:column; align-items:center; justify-content:center; flex:1; padding:32px 24px; gap:20px">
    ${brand(t, 30, 15)}
    <div class="glass" style="width:100%; max-width:400px; padding:28px 28px 24px; display:flex; flex-direction:column; gap:16px; backdrop-filter:blur(14px)">${inner}</div>
    <p class="hint mono" style="margin:0; font-size:11px">Dados da Binance · snapshots diários · horários em UTC</p>
  </div>`;
  return wrap(t, title, body, { w: 480, h });
}
const authCadastro = () => { const t = T; return authCentered('Cadastro', `
  <div><h1 style="margin:0; text-wrap:balance; font-size:22px; font-weight:700; letter-spacing:-.01em; color:${t.textHi}">Criar conta</h1><p class="hint" style="margin:4px 0 0">Você receberá um link para confirmar o e-mail.</p></div>
  ${field(t, 'E-mail', 'voce@exemplo.com', { icon: ic.mail(16) })}
  ${field(t, 'Senha', 'mínimo 8 caracteres', { type: 'password', icon: ic.lock(16) })}
  <div style="display:flex; gap:4px; margin-top:-8px" aria-hidden="true"><i style="flex:1; height:3px; border-radius:2px; background:${t.cyan}"></i><i style="flex:1; height:3px; border-radius:2px; background:${t.cyan}"></i><i style="flex:1; height:3px; border-radius:2px; background:${t.accented}"></i><i style="flex:1; height:3px; border-radius:2px; background:${t.accented}"></i></div>
  <p class="hint" style="margin:-10px 0 0">Força: razoável · use 12+ caracteres com números e símbolos</p>
  ${field(t, 'Confirmar senha', '••••••••••', { type: 'password', icon: ic.lock(16) })}
  <button class="btn primary lg block">Criar conta</button>
  <p class="hint" style="margin:0; text-align:center">Já tem conta? <a href="#">Entrar</a></p>`, 700); };
const authConfirm = () => { const t = T; return authCentered('Verifique seu e-mail', `
  <div style="display:flex; flex-direction:column; align-items:center; text-align:center; gap:12px; padding:8px 0 4px">
    <span style="width:48px; height:48px; border-radius:12px; background:${t.electricSoft}; color:${t.cyan}; display:inline-flex; align-items:center; justify-content:center">${ic.inbox(24)}</span>
    <h1 style="margin:0; text-wrap:balance; font-size:22px; font-weight:700; letter-spacing:-.01em; color:${t.textHi}">Verifique seu e-mail</h1>
    <p style="margin:0; color:${t.textMuted}">Se este e-mail for novo, enviamos um link de confirmação para <span class="mono" style="color:${t.text}">voce@exemplo.com</span>. O link vale por 24 horas.</p>
  </div>
  <div class="hint" style="display:flex; gap:8px; align-items:flex-start; padding:10px 12px; border-radius:8px; background:${t.muted}"><span style="flex:none; color:${t.textDim}; margin-top:1px">${ic.info(14)}</span><span>Não chegou? Confira o spam. Você pode pedir outro link em <span class="mono">0:42</span>.</span></div>
  <button class="btn lg block" disabled style="opacity:.55">Reenviar link</button>
  <p class="hint" style="margin:0; text-align:center"><a href="#">Voltar para entrar</a></p>`); };
const authEsqueci = () => { const t = T; return authCentered('Esqueci a senha', `
  <div><a href="#" class="hint" style="display:inline-flex; align-items:center; gap:4px; margin-bottom:12px">${ic.back(14)}Voltar</a><h1 style="margin:0; text-wrap:balance; font-size:22px; font-weight:700; letter-spacing:-.01em; color:${t.textHi}">Esqueci a senha</h1><p class="hint" style="margin:4px 0 0">Informe o e-mail da conta. Enviaremos um link para criar uma nova senha.</p></div>
  ${field(t, 'E-mail', 'voce@exemplo.com', { icon: ic.mail(16) })}
  <button class="btn primary lg block">Enviar link</button>
  <div role="status" style="display:flex; gap:8px; align-items:flex-start; padding:10px 12px; border-radius:8px; background:${t.muted}; color:${t.textMuted}; font-size:13px"><span style="flex:none; margin-top:1px; color:${t.cyan}">${ic.check(16)}</span><span>Se existir uma conta com este e-mail, você receberá um link em instantes.</span></div>`, 560); };
const authRedefinir = () => { const t = T; return authCentered('Redefinir senha', `
  <div><h1 style="margin:0; text-wrap:balance; font-size:22px; font-weight:700; letter-spacing:-.01em; color:${t.textHi}">Redefinir senha</h1><p class="hint" style="margin:4px 0 0">Crie uma nova senha para <span class="mono">voce@exemplo.com</span>.</p></div>
  ${field(t, 'Nova senha', '••••••••••••', { type: 'password', icon: ic.lock(16) })}
  ${field(t, 'Confirmar nova senha', '••••••••••', { type: 'password', icon: ic.lock(16), err: 'As senhas não coincidem.' })}
  <button class="btn primary lg block">Salvar nova senha</button>
  <div class="hint" style="display:flex; gap:8px; align-items:flex-start; padding:10px 12px; border-radius:8px; background:${t.muted}"><span style="flex:none; color:${t.textDim}; margin-top:1px">${ic.info(14)}</span><span>Link expirado ou inválido? <a href="#">Peça um novo</a>.</span></div>`, 560); };

// ---------- Tela 2: Home ----------
function insightCard(t, { icon, title, sub, rows, ai = false }) {
  return `<section class="glass" aria-label="${title}" style="flex:1; min-width:0; display:flex; flex-direction:column; overflow:hidden">
    <div style="display:flex; align-items:center; gap:10px; padding:13px 16px 11px; border-bottom:1px solid ${t.borderMuted}">
      <span style="flex:none; width:32px; height:32px; border-radius:8px; background:${ai ? t.cyanSoft : t.electricSoft}; border:1px solid ${ai ? 'rgba(95,196,255,.35)' : 'rgba(62,134,247,.3)'}; color:${ai ? t.cyan : t.electric}; display:inline-flex; align-items:center; justify-content:center">${icon}</span>
      <span style="flex:1; min-width:0"><span style="display:block; font-weight:700; color:${t.textHi}">${title}</span><span class="hint" style="font-size:11.5px">${sub}</span></span>
      ${ai ? `<span class="chip ai" style="font-size:10px">${ic.sparkle(11)} IA · v0</span>` : ''}
    </div>
    ${rows.map(([sym, name, main, delta, dir], i) => `<a href="#" style="display:flex; align-items:center; gap:10px; padding:9px 16px; text-decoration:none; color:inherit; border-bottom:1px solid ${i < rows.length - 1 ? t.borderMuted : 'transparent'}">
      <span class="mono" style="flex:none; width:16px; font-size:11px; color:${t.textDim}">${i + 1}</span>
      <span style="flex:1; min-width:0"><span class="mono" translate="no" style="display:block; font-weight:500; color:${t.textHi}; font-size:13px">${sym}</span><span class="hint" style="font-size:11px">${name}</span></span>
      <span style="display:flex; flex-direction:column; align-items:flex-end"><span class="mono" style="font-size:13px; color:${t.text}">${main}</span><span class="mono" style="font-size:11.5px; color:${dir === 'up' ? t.ice : dir === 'down' ? t.down : t.cyan}">${delta}</span></span>
    </a>`).join('')}
  </section>`;
}

function home() {
  const t = T; const W = 1440, H = 960;
  const vol = [['SOLUSDT', 'Solana', 'ATR 5,8 %', '▲ +3,11 %', 'up'], ['SUIUSDT', 'Sui', 'ATR 5,1 %', '▲ +5,78 %', 'up'], ['DOGEUSDT', 'Dogecoin', 'ATR 4,7 %', '+0,00 %', ''], ['ADAUSDT', 'Cardano', 'ATR 4,2 %', '▼ −2,25 %', 'down'], ['LINKUSDT', 'Chainlink', 'ATR 4,0 %', '▲ +3,91 %', 'up']];
  const gap = [['ETHUSDT', 'Ethereum', 'real 4.312,9', 'gap +4,6 %', 'ai'], ['XRPUSDT', 'XRP', 'real 3,0120', 'gap −3,8 %', 'ai'], ['BNBUSDT', 'BNB', 'real 842,10', 'gap +2,9 %', 'ai'], ['BTCUSDT', 'Bitcoin', 'real 113.512', 'gap +1,2 %', 'ai'], ['AVAXUSDT', 'Avalanche', 'real 26,05', 'gap −1,1 %', 'ai']];
  const volu = [['BTCUSDT', 'Bitcoin', '4,33 bi USDT', '▲ +18 % vs média', 'up'], ['ETHUSDT', 'Ethereum', '2,65 bi USDT', '▲ +9 % vs média', 'up'], ['SOLUSDT', 'Solana', '1,81 bi USDT', '▲ +41 % vs média', 'up'], ['XRPUSDT', 'XRP', '1,22 bi USDT', '▼ −6 % vs média', 'down'], ['BNBUSDT', 'BNB', '1,02 bi USDT', '▼ −2 % vs média', 'down']];
  const body = `
  ${header(t, { active: 'home' })}
  <main style="flex:1; min-height:0; padding:24px 24px; display:flex; flex-direction:column; gap:16px; overflow:hidden">
    <div style="display:flex; align-items:flex-end; justify-content:space-between; gap:16px; flex-wrap:wrap">
      <div>
        <p class="eyebrow" style="margin:0 0 6px; color:${t.cyan}">Bem-vindo novamente, Gabriel</p>
        <h1 style="margin:0; text-wrap:balance; font-size:24px; font-weight:700; letter-spacing:-.01em; color:${t.textHi}">As principais mudanças no mercado desde o seu último acesso</h1>
        <p class="hint" style="margin:6px 0 0">Último acesso em 17 ago 22:14 UTC · comparando com o snapshot de 19 ago 14:00 UTC</p>
      </div>
      <div style="display:flex; gap:8px; align-items:center">${stamp(t, { label: 'Resumo 24h: 19 ago 14:00 UTC · há 12 min' })}<button class="btn" aria-label="Atualizar">${ic.refresh(14)}<span>Atualizar</span></button></div>
    </div>
    <div style="display:flex; gap:16px; min-height:0">
      ${insightCard(t, { icon: ic.wave(16), title: 'Maior volatilidade de preço', sub: 'ATR 14 relativo · desde o seu último acesso', rows: vol })}
      ${insightCard(t, { icon: ic.gap(16), title: 'Maior gap real × projeção', sub: 'diferença entre preço real e previsão diária', rows: gap, ai: true })}
      ${insightCard(t, { icon: ic.volume(16), title: 'Maior volume de transação', sub: 'volume 24h em USDT vs média de 7 dias', rows: volu })}
    </div>
    <section class="glass-hi" style="display:flex; align-items:center; gap:16px; padding:15px 20px">
      <span style="flex:none; width:38px; height:38px; border-radius:10px; background:${t.cyanSoft}; border:1px solid rgba(95,196,255,.35); color:${t.cyan}; display:inline-flex; align-items:center; justify-content:center">${ic.sparkle(18)}</span>
      <div style="flex:1; min-width:0">
        <span style="display:block; font-weight:700; color:${t.textHi}">Leitura do dia, pelo modelo</span>
        <p style="margin:3px 0 0; font-size:13px; color:${t.textMuted}; max-width:110ch">O mercado abriu comprador: 14 dos 20 ativos rastreados subiram nas últimas 24 h. O maior descolamento entre preço e projeção está em <a href="#" translate="no">ETHUSDT</a> (previsão 4,6 % acima do preço atual). Solana segue como o ativo mais volátil da semana.</p>
      </div>
      <a href="#" class="btn" style="flex:none">Ver previsões</a>
    </section>
    <section style="display:flex; gap:16px">
      <a href="#" class="glass" style="flex:1; display:flex; align-items:center; gap:14px; padding:14px 18px; text-decoration:none; color:inherit">
        <span style="color:${t.electric}">${ic.candle(22)}</span>
        <span style="flex:1"><span style="display:block; font-weight:500; color:${t.textHi}">Continuar de onde parou</span><span class="hint"><span translate="no">BTCUSDT</span> · 1h · SMA 20/50, RSI e MACD ligados</span></span>
        <span style="color:${t.textDim}">${ic.fwd(16)}</span>
      </a>
      <a href="#" class="glass" style="flex:1; display:flex; align-items:center; gap:14px; padding:14px 18px; text-decoration:none; color:inherit">
        <span style="color:${t.electric}">${ic.bell(20)}</span>
        <span style="flex:1"><span style="display:block; font-weight:500; color:${t.textHi}">Configurar alertas</span><span class="hint">Escolha os tópicos que aparecem neste painel</span></span>
        <span style="color:${t.textDim}">${ic.fwd(16)}</span>
      </a>
    </section>
  </main>`;
  return wrap(t, 'Início', body, { w: W, h: H });
}

function homeMobile() {
  const t = T; const W = 390, H = 844;
  const cards = [
    ['Maior volatilidade', '', [['SOLUSDT', 'ATR 5,8 %', '▲ +3,11 %', 'up'], ['SUIUSDT', 'ATR 5,1 %', '▲ +5,78 %', 'up']]],
    ['Maior gap real × projeção', 'ai', [['ETHUSDT', 'real 4.312,9', 'gap +4,6 %', 'ai'], ['XRPUSDT', 'real 3,0120', 'gap −3,8 %', 'ai']]],
    ['Maior volume', '', [['BTCUSDT', '4,33 bi USDT', '▲ +18 %', 'up'], ['SOLUSDT', '1,81 bi USDT', '▲ +41 %', 'up']]],
  ];
  const body = `
  ${header(t, { mobile: true })}
  <div style="flex:1; min-height:0; overflow:hidden; padding:16px 12px 80px; display:flex; flex-direction:column; gap:12px">
    <div>
      <p class="eyebrow" style="margin:0 0 4px; color:${t.cyan}">Bem-vindo novamente, Gabriel</p>
      <h1 style="margin:0; text-wrap:balance; font-size:19px; font-weight:700; color:${t.textHi}">Mudanças desde o seu último acesso</h1>
      <p class="hint mono" style="margin:4px 0 0; font-size:11px">último acesso 17 ago 22:14 UTC</p>
    </div>
    ${cards.map(([title, kind, rows]) => `<section class="glass" aria-label="${title}" style="overflow:hidden">
      <div style="display:flex; align-items:center; justify-content:space-between; padding:11px 14px 9px; border-bottom:1px solid ${t.borderMuted}"><span style="font-weight:700; color:${t.textHi}; font-size:13.5px">${title}</span>${kind === 'ai' ? `<span class="chip ai" style="font-size:10px">${ic.sparkle(11)} IA · v0</span>` : `<span class="hint mono" style="font-size:10.5px">24h</span>`}</div>
      ${rows.map((r, ri) => `<a href="#" style="display:flex; align-items:center; gap:10px; padding:10px 14px; min-height:48px; text-decoration:none; color:inherit; border-bottom:1px solid ${ri === 0 ? t.borderMuted : 'transparent'}"><span class="mono" style="width:14px; font-size:11px; color:${t.textDim}">${ri + 1}</span><span class="mono" translate="no" style="flex:1; font-weight:500; color:${t.textHi}; font-size:13.5px">${r[0]}</span><span style="display:flex; flex-direction:column; align-items:flex-end"><span class="mono" style="font-size:12.5px">${r[1]}</span><span class="mono" style="font-size:11px; color:${r[3] === 'up' ? t.ice : r[3] === 'down' ? t.down : t.cyan}">${r[2]}</span></span></a>`).join('')}
      <a href="#" class="hint" style="display:block; padding:9px 14px; border-top:1px solid ${t.borderMuted}; font-size:12px">Ver top 5</a>
    </section>`).join('')}
  </div>
  ${mobileTabs(t, 'home')}`;
  return wrap(t, 'Início mobile', body, { w: W, h: H });
}

// ---------- Gráficos ----------
function graficos() {
  const t = T; const W = 1440, H = 960;
  const chartW = W - 48 - 268 - 16; const chartH = 652;
  const body = `
  ${header(t, { active: 'graficos' })}
  <h1 style="position:absolute; width:1px; height:1px; overflow:hidden; clip:rect(0 0 0 0); margin:-1px">Gráficos</h1>
  ${toolbar(t, {})}
  <main style="display:flex; gap:16px; padding:0 24px 16px; flex:1; min-height:0">
    <section class="glass" aria-label="Gráfico de velas com cenários do modelo" style="flex:1; position:relative; overflow:hidden; display:flex; flex-direction:column">
      <div style="position:relative; height:${chartH}px;">
        ${chartSvg(t, chartW, chartH, { overlays: ['sma20', 'sma50'], panes: ['rsi', 'macd'], cut: true, forecast: true })}
        ${legend(t, { rows: [['SMA 20', t.sma20, '113.512,3', ''], ['SMA 50', t.sma50, '112.980,7', 'warm-up até 16 ago']] })}
      </div>
      <div style="display:flex; align-items:center; justify-content:space-between; padding:8px 14px; border-top:1px solid ${t.border}; font-size:11px; color:${t.textDim}" class="mono"><span>Eixo em UTC · arraste para navegar · scroll para zoom · <span style="color:${t.cyan}">┆</span> corte = último dado · à direita, cenários do modelo</span><span>exibindo 92 de 720 velas · retenção 30 dias</span></div>
    </section>
    ${togglesPanel(t, {})}
  </main>
  <div style="padding:0 24px 24px">${kpiStrip(t)}</div>`;
  return wrap(t, 'Gráficos', body, { w: W, h: H });
}

function graficosMobile() {
  const t = T; const W = 390, H = 844;
  const body = `
  ${header(t, { mobile: true })}
  <div style="display:flex; flex-direction:column; gap:8px; padding:10px 12px 0; flex:none">
    <div style="display:flex; gap:8px"><button class="btn" style="flex:1; height:40px; justify-content:space-between"><span style="display:inline-flex; gap:8px; align-items:center">${ic.search(14)}<span class="mono" translate="no" style="font-weight:500; color:${t.textHi}">BTCUSDT</span></span>${ic.chevron(14)}</button><div role="radiogroup" aria-label="Timeframe" style="display:inline-flex; gap:2px; padding:2px; background:rgba(4,8,18,.5); border:1px solid ${t.border}; border-radius:8px">${['15m', '1h', '1d'].map(k => `<button class="btn mono" style="height:34px; border:none; border-radius:6px; padding:0 10px; background:${k === '1h' ? t.electricSoft : 'transparent'}; color:${k === '1h' ? t.cyan : t.textMuted}">${k}</button>`).join('')}</div></div>
    <div style="display:flex; gap:8px; align-items:center; justify-content:space-between">${stamp(t, { mobile: true })}<button class="btn" aria-label="Atualizar" style="width:40px; padding:0; height:34px">${ic.refresh(16)}</button></div>
  </div>
  <section class="glass" style="margin:10px 12px 0; position:relative; overflow:hidden; height:420px; flex:none">
    ${chartSvg(t, 364, 420, { mobile: true, show: 48, panes: ['rsi'], crossAt: 0.58, forecast: true })}
    ${legend(t, { mobile: true, rows: [['SMA 20', t.sma20, '113.512', ''], ['SMA 50', t.sma50, '112.981', '']], forecastChip: false })}
  </section>
  <div style="padding:10px 12px 118px; flex:none">${kpiStrip(t, { mobile: true })}</div>
  <div style="position:absolute; left:0; right:0; bottom:64px; display:flex; justify-content:center; padding:6px 0"><button class="btn" aria-haspopup="dialog" style="height:32px; font-size:12px; backdrop-filter:blur(8px)">${ic.sliders(14)}<span>Indicadores</span></button></div>
  ${mobileTabs(t, 'graficos')}`;
  return wrap(t, 'Gráficos mobile', body, { w: W, h: H });
}

function drawerMobile() {
  const t = T; const W = 390, H = 844;
  const body = `
  ${header(t, { mobile: true })}
  <div style="position:absolute; inset:0; background:rgba(2,4,10,.6)"></div>
  <div class="glass" role="dialog" aria-label="Indicadores" style="position:absolute; left:0; right:0; bottom:0; border-radius:16px 16px 0 0; padding:8px 12px 22px; display:flex; flex-direction:column; gap:4px; backdrop-filter:blur(18px)">
    <div style="width:40px; height:4px; border-radius:999px; background:${t.accented}; margin:2px auto 8px"></div>
    <div style="display:flex; justify-content:space-between; align-items:center; padding:0 4px 8px"><span style="font-weight:700; color:${t.textHi}; font-size:15px">Indicadores</span><button class="btn ghost" aria-label="Fechar" style="width:36px; padding:0">${ic.x(18)}</button></div>
    ${[['SMA 20', t.sma20, true, 'solid'], ['SMA 50', t.sma50, true, 'solid'], ['SMA 200', t.sma200, false, 'solid'], ['EMA 12', t.ema12, false, 'dash'], ['EMA 26', t.ema26, false, 'dash'], ['Bollinger 20·2', t.bb, false, 'dot'], ['Volume', t.textDim, true, 'solid'], ['RSI 14', t.rsi, true, 'solid'], ['MACD 12·26·9', t.sma20, false, 'solid'], ['Previsão IA (cenários)', t.cyan, true, 'dash']].map(([l, c, on, st]) => `<label style="display:flex; align-items:center; gap:12px; height:44px; padding:0 4px; border-bottom:1px solid ${t.borderMuted}"><span style="width:20px; height:0; border-top:2px ${st === 'dash' ? 'dashed' : st === 'dot' ? 'dotted' : 'solid'} ${c}"></span><span style="flex:1; font-size:14px; color:${on ? t.text : t.textMuted}">${l}</span><span role="switch" tabindex="0" aria-checked="${on}" style="width:40px; height:24px; border-radius:999px; background:${on ? t.electric : t.accented}; position:relative; display:inline-block"><i style="position:absolute; top:3px; ${on ? 'right:3px' : 'left:3px'}; width:18px; height:18px; border-radius:999px; background:#f6f9fd; display:block"></i></span></label>`).join('')}
    <div class="hint" style="padding:10px 4px 0; display:flex; gap:6px">${ic.info(14)}<span>Linhas começam só depois da janela de cálculo (warm-up).</span></div>
  </div>`;
  return wrap(t, 'Indicadores (drawer mobile)', body, { w: W, h: H });
}

// ---------- Previsões ----------
function previsoes() {
  const t = T; const W = 1440, H = 1080;
  const rows = [
    ['BTCUSDT', '113.512,3', '114.890 · +1,2 %', '116.400 · +2,5 %', '121.900 · +7,4 %', '138.500 · +22,0 %', 82],
    ['ETHUSDT', '4.312,9', '4.511 · +4,6 %', '4.630 · +7,4 %', '4.890 · +13,4 %', '5.720 · +32,6 %', 74],
    ['SOLUSDT', '186,40', '191,2 · +2,6 %', '198,4 · +6,4 %', '210,0 · +12,7 %', '241,0 · +29,3 %', 68],
    ['XRPUSDT', '3,0120', '2,897 · −3,8 %', '2,850 · −5,4 %', '3,120 · +3,6 %', '3,610 · +19,9 %', 61],
    ['BNBUSDT', '842,10', '866,5 · +2,9 %', '881,0 · +4,6 %', '902,0 · +7,1 %', '990,0 · +17,6 %', 77],
    ['DOGEUSDT', '0,2310', '0,2295 · −0,6 %', '0,2410 · +4,3 %', '0,2550 · +10,4 %', '0,2900 · +25,5 %', 55],
    ['ADAUSDT', '0,9120', '0,9010 · −1,2 %', '0,9330 · +2,3 %', '0,9800 · +7,5 %', '1,1400 · +25,0 %', 59],
    ['LINKUSDT', '24,18', '24,90 · +3,0 %', '25,60 · +5,9 %', '27,10 · +12,1 %', '31,50 · +30,3 %', 71],
    ['AVAXUSDT', '26,05', '26,40 · +1,3 %', '27,00 · +3,6 %', '28,20 · +8,3 %', '31,90 · +22,5 %', 64],
    ['TRXUSDT', '0,3520', '0,3560 · +1,1 %', '0,3610 · +2,6 %', '0,3700 · +5,1 %', '0,4100 · +16,5 %', 69],
    ['SUIUSDT', '3,842', '3,990 · +3,9 %', '4,120 · +7,2 %', '4,350 · +13,2 %', '5,010 · +30,4 %', 58],
    ['LTCUSDT', '118,40', '117,20 · −1,0 %', '120,10 · +1,4 %', '124,60 · +5,2 %', '139,00 · +17,4 %', 66],
  ];
  const body = `
  ${header(t, { active: 'previsoes' })}
  <main style="flex:1; min-height:0; padding:20px 24px 24px; display:flex; flex-direction:column; gap:14px; overflow:hidden">
    <div style="display:flex; align-items:flex-end; justify-content:space-between; gap:16px; flex-wrap:wrap">
      <div>
        <h1 style="margin:0; text-wrap:balance; font-size:24px; font-weight:700; letter-spacing:-.01em; color:${t.textHi}">Previsões do modelo</h1>
        <p class="hint" style="margin:6px 0 0">Top 20 ativos calculados · horizonte diário, semanal, mensal e anual · treinado em 19 ago 00:40 UTC</p>
      </div>
      <div style="display:flex; gap:8px; align-items:center">
        <span class="chip ai">${ic.sparkle(12)} Prophet · v0.3 · em validação</span>
        <span class="chip" title="Erro absoluto médio da última rodada de backtesting">MAE 412,3 USDT</span>
        <span class="chip" title="Acertos de direção (sobe ou desce) na última rodada">direção 63 %</span>
        <button class="btn">${ic.refresh(14)}<span>Atualizar</span></button>
      </div>
    </div>
    <section class="glass-hi" style="display:flex; gap:16px; align-items:flex-start; padding:15px 20px">
      <span style="flex:none; width:38px; height:38px; border-radius:10px; background:${t.cyanSoft}; border:1px solid rgba(95,196,255,.35); color:${t.cyan}; display:inline-flex; align-items:center; justify-content:center">${ic.sparkle(18)}</span>
      <div style="min-width:0">
        <span style="display:block; font-weight:700; color:${t.textHi}">Resumo da rodada, em texto</span>
        <p style="margin:4px 0 0; font-size:13px; color:${t.textMuted}; max-width:120ch">Para amanhã, o modelo espera alta média de 1,4 % nos 20 ativos. Os três maiores descolamentos entre preço e projeção diária são <a href="#" translate="no">ETHUSDT</a> (+4,6 %), <a href="#" translate="no">XRPUSDT</a> (−3,8 %) e <a href="#" translate="no">LINKUSDT</a> (+3,0 %). No horizonte anual a projeção média é +24 %, com confiança menor: o erro cresce com o horizonte. Leia as previsões como cenários, não como recomendação de compra ou venda.</p>
      </div>
    </section>
    <section class="glass" style="flex:1; min-height:0; overflow:hidden; display:flex; flex-direction:column">
      <div style="overflow:auto">
      <table class="tbl" aria-label="Previsões por ativo">
        <thead><tr>
          <th scope="col" tabindex="0" style="position:sticky; left:0; background:${t.solid}">Ativo</th><th scope="col" tabindex="0">Preço real</th>
          <th scope="col" tabindex="0" aria-sort="none">Previsão diária</th><th scope="col" tabindex="0">Semanal</th><th scope="col" tabindex="0">Mensal</th><th scope="col" tabindex="0">Anual</th><th scope="col" tabindex="0" title="Confiança do modelo para o horizonte diário, medida no backtesting">Confiança</th>
        </tr></thead>
        <tbody>${rows.map(([s, real, d, w2, m, y, conf], ri) => `<tr class="${ri === 1 ? 'sel' : ''}" tabindex="0">
          <td translate="no" style="position:sticky; left:0; background:${ri === 1 ? 'rgba(62,134,247,.10)' : t.solid}; font-weight:500; color:${t.textHi}">${s}</td>
          <td>${real}</td>
          ${[d, w2, m, y].map(v => `<td><span style="color:${v.includes('−') ? t.down : t.ice}">${v}</span></td>`).join('')}
          <td><span class="mono" style="color:${conf >= 70 ? t.cyan : t.textMuted}">${conf} %</span></td>
        </tr>`).join('')}</tbody>
      </table>
      </div>
      <div style="display:flex; justify-content:space-between; padding:9px 14px; border-top:1px solid ${t.border}; margin-top:auto" class="hint"><span>20 ativos (12 visíveis, rola) · previsão em USDT · % vs preço real · ordenável por coluna</span><span class="mono">gelo = projeção acima do real · vermelho = abaixo</span></div>
    </section>
    <div style="display:flex; gap:16px">
      <section class="glass" style="flex:1.4; display:flex; gap:14px; align-items:center; padding:14px 18px">
        <span style="flex:none; color:${t.cyan}">${ic.wave(22)}</span>
        <div style="flex:1; min-width:0">
          <span style="display:block; font-weight:700; color:${t.textHi}">Simulação de Monte Carlo com backtesting <span class="chip" style="margin-left:8px; font-size:10px">Em breve</span></span>
          <p class="hint" style="margin:3px 0 0; max-width:80ch">Milhares de trajetórias simuladas por ativo para mostrar o melhor e o pior cenário do modelo, com o histórico de acertos por rodada.</p>
        </div>
      </section>
      <section class="glass" style="flex:1; display:flex; gap:14px; align-items:center; padding:14px 18px">
        <span style="flex:none; color:${t.electric}">${ic.candle(22)}</span>
        <div style="flex:1; min-width:0">
          <span style="display:block; font-weight:700; color:${t.textHi}">Cenários sobre o gráfico</span>
          <p class="hint" style="margin:3px 0 0">As linhas de melhor caso, esperada e pior caso já aparecem no gráfico de velas, depois da linha de corte.</p>
        </div>
        <a href="#" class="btn" style="flex:none">Abrir gráfico</a>
      </section>
    </div>
  </main>`;
  return wrap(t, 'Previsões', body, { w: W, h: H });
}

// ---------- Mercado ----------
function mercado() {
  const t = T; const W = 1440, H = 900;
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
  ];
  const cols = ['Ativo', 'Último', 'Var. 24h', 'Var. %', 'Preço médio', 'Abertura', 'Máxima', 'Mínima', 'Bid', 'Ask', 'Volume (base)', 'Volume (USDT) ▼', 'Trades'];
  const body = `
  ${header(t, { active: 'mercado' })}
  <div style="display:flex; align-items:flex-end; justify-content:space-between; padding:20px 24px 12px; gap:16px; flex-wrap:wrap">
    <div><h1 style="margin:0; text-wrap:balance; font-size:24px; font-weight:700; letter-spacing:-.01em; color:${t.textHi}">Mercado · resumo 24h</h1><p class="hint" style="margin:6px 0 0">Top 20 pares USDT por volume. Clique em um ativo para abri-lo no gráfico.</p></div>
    <div style="display:flex; gap:8px; align-items:center">
      <div class="input" style="height:34px; width:220px; font-size:13px"><span style="color:${t.textDim}">${ic.search(14)}</span><span class="ph">Filtrar ativo…</span></div>
      ${stamp(t, { label: 'Resumo 24h: 19 ago 14:00 UTC · há 12 min' })}
      <button class="btn">${ic.refresh(14)}<span>Atualizar</span></button>
    </div>
  </div>
  <section class="glass" style="margin:0 24px 24px; overflow:hidden; flex:1; min-height:0; display:flex; flex-direction:column">
    <div style="overflow:auto">
    <table class="tbl" aria-label="Resumo 24h por ativo">
      <thead><tr>${cols.map((c, i) => `<th scope="col" tabindex="0" aria-sort="${i === 11 ? 'descending' : 'none'}" style="${i === 11 ? `color:${t.textHi}` : ''}; ${i === 0 ? 'position:sticky; left:0; background:' + t.solid : ''}">${c}</th>`).join('')}</tr></thead>
      <tbody>${rows.map((r, ri) => `<tr class="${ri === 0 ? 'sel' : ri === 2 ? 'hover' : ''}" tabindex="0">${r.map((v, ci) => { let style = ci === 0 ? `position:sticky; left:0; background:${ri === 0 ? 'rgba(62,134,247,.10)' : ri === 2 ? t.solid2 : t.solid}; font-weight:500; color:${t.textHi}` : ''; let cell = v; if (ci === 3 && v !== '—') { const up = v.startsWith('+') && v !== '+0,00'; const dn = v.startsWith('−'); cell = `<span style="color:${up ? t.ice : dn ? t.down : t.textMuted}">${up ? '▲ ' : dn ? '▼ ' : ''}${v} %</span>`; } if (ci === 2 && v !== '—') { cell = `<span style="color:${v.startsWith('+') ? t.ice : v.startsWith('−') ? t.down : t.textMuted}">${v}</span>`; } if (v === '—') cell = `<span style="color:${t.textDim}" title="Sem snapshot recente para este ativo">—</span>`; if (ci === 0) cell = `<span translate="no">${v}</span>` + (ri === 8 ? ` <span class="hint mono" style="font-size:10px; font-weight:400">sem dados</span>` : ''); return `<td style="${style}">${cell}</td>`; }).join('')}</tr>`).join('')}</tbody>
    </table></div>
    <div style="display:flex; justify-content:space-between; padding:9px 14px; border-top:1px solid ${t.border}; margin-top:auto" class="hint"><span>20 ativos (12 visíveis, rola) · ordenado por volume (USDT) desc · cabeçalhos ordenáveis (Enter/Espaço)</span><span class="mono">▲ alta · ▼ baixa · sem seta = sem variação · — = sem dados</span></div>
  </section>`;
  return wrap(t, 'Mercado', body, { w: W, h: H });
}

function mercadoMobile() {
  const t = T; const W = 390, H = 844;
  const rows = [['BTCUSDT', 'Bitcoin', '113.512,3', '+1,84', '4,33 bi', true], ['ETHUSDT', 'Ethereum', '4.312,9', '−0,62', '2,65 bi'], ['SOLUSDT', 'Solana', '186,40', '+3,11', '1,81 bi'], ['XRPUSDT', 'XRP', '3,0120', '−1,05', '1,22 bi'], ['BNBUSDT', 'BNB', '842,10', '+0,20', '1,02 bi'], ['DOGEUSDT', 'Dogecoin', '0,2310', '+0,00', '896 mi'], ['ADAUSDT', 'Cardano', '0,9120', '−2,25', '656 mi'], ['PEPEUSDT', 'Pepe', '—', '—', '—'], ['LINKUSDT', 'Chainlink', '24,18', '+3,91', '509 mi']];
  const body = `
  ${header(t, { mobile: true })}
  <div style="padding:14px 12px 8px; display:flex; flex-direction:column; gap:8px; flex:none">
    <div style="display:flex; justify-content:space-between; align-items:baseline"><span style="font-size:18px; font-weight:700; color:${t.textHi}">Mercado</span><span class="hint mono" style="font-size:11px">24h · 14:00 UTC · há 12 min</span></div>
    <div style="display:flex; gap:8px"><div class="input" style="flex:1; height:40px"><span style="color:${t.textDim}">${ic.search(14)}</span><span class="ph">Filtrar ativo…</span></div><button class="btn" style="height:40px">${ic.sort(14)}<span>Volume</span>${ic.chevron(14)}</button></div>
  </div>
  <div class="glass" style="margin:0 12px 80px; overflow:hidden">
    ${rows.map(([s, n, p, v, vol, sel]) => { const up = v.startsWith('+') && v !== '+0,00'; const dn = v.startsWith('−'); const nul = v === '—'; return `<a href="#" style="display:flex; align-items:center; justify-content:space-between; padding:10px 14px; min-height:56px; border-bottom:1px solid ${t.borderMuted}; background:${sel ? 'rgba(62,134,247,.10)' : 'transparent'}; text-decoration:none; color:inherit"><span style="display:flex; flex-direction:column"><span class="mono" translate="no" style="font-weight:500; color:${t.textHi}; font-size:14px">${s}</span><span class="hint">${n} · vol ${vol}</span></span><span style="display:flex; flex-direction:column; align-items:flex-end"><span class="mono" style="font-size:14px; color:${nul ? t.textDim : t.textHi}">${p}</span><span class="mono" style="font-size:12px; color:${nul ? t.textDim : up ? t.ice : dn ? t.down : t.textMuted}">${nul ? 'sem dados' : `${up ? '▲ ' : dn ? '▼ ' : ''}${v} %`}</span></span></a>`; }).join('')}
  </div>
  ${mobileTabs(t, 'mercado')}`;
  return wrap(t, 'Mercado mobile', body, { w: W, h: H });
}

// ---------- Preferências ----------
function preferencias() {
  const t = T; const W = 1440, H = 900;
  const sw = on => `<span role="switch" tabindex="0" aria-checked="${on}" style="width:44px; height:26px; border-radius:999px; background:${on ? t.electric : t.accented}; position:relative; display:inline-block; flex:none"><i style="position:absolute; top:3px; ${on ? 'right:3px' : 'left:3px'}; width:20px; height:20px; border-radius:999px; background:#f6f9fd; display:block"></i></span>`;
  const cb = (label, desc, on) => `<label style="display:flex; gap:12px; align-items:flex-start; padding:12px 0; border-bottom:1px solid ${t.borderMuted}; cursor:pointer"><span role="checkbox" tabindex="0" aria-checked="${on}" style="flex:none; margin-top:2px; width:18px; height:18px; border-radius:5px; border:1px solid ${on ? t.electric : t.border}; background:${on ? t.electric : 'transparent'}; color:#04070f; display:inline-flex; align-items:center; justify-content:center">${on ? ic.check(13) : ''}</span><span style="flex:1"><span style="display:block; font-weight:500; color:${t.textHi}">${label}</span><span class="hint">${desc}</span></span></label>`;
  const body = `
  ${header(t, { active: 'none' })}
  <main style="flex:1; min-height:0; padding:20px 24px; display:flex; flex-direction:column; gap:14px; overflow:hidden">
    <div><h1 style="margin:0; text-wrap:balance; font-size:24px; font-weight:700; letter-spacing:-.01em; color:${t.textHi}">Preferências</h1><p class="hint" style="margin:6px 0 0">Seus dados e o que você quer receber deste painel.</p></div>
    <div style="display:flex; gap:16px; min-height:0; align-items:stretch">
      <section class="glass" aria-label="Dados pessoais" style="flex:1; padding:20px 22px; display:flex; flex-direction:column; gap:14px">
        <div style="display:flex; align-items:center; gap:10px"><span style="color:${t.electric}">${ic.user(18)}</span><span style="font-weight:700; color:${t.textHi}; font-size:15px">Dados pessoais</span></div>
        ${field(t, 'Nome', 'Gabriel Castro', {})}
        ${field(t, 'E-mail', 'gabriel@exemplo.com', { icon: ic.mail(16) })}
        ${field(t, 'Telefone celular', '+55 (11) 9 8123-4567', { icon: ic.phone(16) })}
        <p class="hint" style="margin:-4px 0 0">O telefone só será usado para alertas por SMS ou WhatsApp, quando você ativar.</p>
        <div style="display:flex; gap:8px"><button class="btn primary">Salvar alterações</button><button class="btn ghost">Descartar</button></div>
        <div style="border-top:1px solid ${t.borderMuted}; padding-top:12px; display:flex; flex-direction:column; gap:8px">
          <span style="font-weight:500; color:${t.textHi}">Acessibilidade</span>
          <label style="display:flex; justify-content:space-between; align-items:center; gap:12px; cursor:pointer"><span><span style="display:block; font-weight:500; color:${t.textHi}; font-size:13px">Velas de alta preenchidas</span><span class="hint">Preenche o corpo das velas de alta (padrão: vazadas, estilo vidro)</span></span>${sw(false)}</label>
        </div>
      </section>
      <section class="glass" aria-label="Notificações" style="flex:1.2; padding:20px 22px; display:flex; flex-direction:column; min-height:0">
        <div style="display:flex; align-items:center; justify-content:space-between; gap:12px; padding-bottom:13px; border-bottom:1px solid ${t.border}">
          <span style="display:flex; align-items:center; gap:10px"><span style="color:${t.electric}">${ic.bell(18)}</span><span><span style="display:block; font-weight:700; color:${t.textHi}; font-size:15px">Notificações</span><span class="hint">Resumo diário com os tópicos que você escolher</span></span></span>
          ${sw(true)}
        </div>
        <div style="padding-top:4px">
          ${cb('Maiores gaps entre preço real e projeção', 'Quando a previsão do modelo descolar mais de 3 % do preço', true)}
          ${cb('Ativos com maior movimentação de volume diário', 'Volume 24h muito acima da média de 7 dias', true)}
          ${cb('Maior volatilidade diária de preço', 'ATR relativo no topo do ranking dos 20 ativos', false)}
          ${cb('Novas rodadas do modelo', 'Quando previsões e métricas forem recalculadas', false)}
        </div>
        <div style="margin-top:auto; padding-top:12px; display:flex; flex-direction:column; gap:10px">
          <span style="font-weight:500; color:${t.textHi}">Canal de envio</span>
          <div style="display:flex; gap:8px; flex-wrap:wrap">
            <span class="chip" style="height:32px; padding:0 12px; border-color:${t.electric}; color:${t.cyan}; background:${t.electricSoft}">${ic.mail(14)} E-mail</span>
            <span class="chip" style="height:32px; padding:0 12px; opacity:.7">${ic.phone(14)} SMS <span style="font-size:10px; margin-left:4px; padding:1px 6px; border-radius:999px; border:1px solid ${t.border}">Em breve</span></span>
            <span class="chip" style="height:32px; padding:0 12px; opacity:.7">${ic.phone(14)} WhatsApp <span style="font-size:10px; margin-left:4px; padding:1px 6px; border-radius:999px; border:1px solid ${t.border}">Em breve</span></span>
          </div>
          <p class="hint" style="margin:0">Os alertas seguem o ritmo do pipeline (1x/dia). Nada é tempo real.</p>
        </div>
      </section>
    </div>
  </main>`;
  return wrap(t, 'Preferências', body, { w: W, h: H });
}

// ---------- Estados ----------
function estados() {
  const t = T; const W = 1440, H = 900; const pw = (W - 48 - 16 * 2) / 3, ph = 340;
  const panel = (title, sub, inner) => `<div style="display:flex; flex-direction:column; gap:8px; width:${pw}px"><div><div style="font-weight:700; color:${t.textHi}">${title}</div><div class="hint">${sub}</div></div><div class="glass" style="height:${ph}px; position:relative; overflow:hidden">${inner}</div></div>`;
  const center = (icon, h, p, btn = '') => `<div style="position:absolute; inset:0; display:flex; flex-direction:column; align-items:center; justify-content:center; text-align:center; gap:8px; padding:24px"><span style="color:${t.textDim}">${icon}</span><div style="font-weight:700; color:${t.textHi}">${h}</div><p class="hint" style="margin:0; max-width:300px">${p}</p>${btn}</div>`;
  const skel = `<div style="position:absolute; left:12px; top:10px; display:flex; gap:8px"><span class="sk" style="width:72px; height:12px"></span><span class="sk" style="width:160px; height:12px"></span></div>${chartSvg(t, pw - 2, ph - 2, { skeleton: true, panes: ['rsi'], crossAt: 0, cut: false, forecast: false })}<div class="hint mono" style="position:absolute; left:12px; bottom:10px; font-size:11px">Carregando BTCUSDT · 1h…</div>`;
  const warm = `${chartSvg(t, pw - 2, ph - 2, { show: 60, total: 70, overlays: ['sma20', 'sma50'], panes: ['rsi'], crossAt: 0, cut: true, forecast: false, seed: 11, padTop: 108 })}${legend(t, { tf: '1h', mobile: true, forecastChip: false, rows: [['SMA 20', t.sma20, '111.204,0', ''], ['SMA 50', t.sma50, '—', 'warm-up · a partir de 04 ago'], ['SMA 200', t.sma200, '—', 'warm-up · faltam 140 velas']] })}`;
  const stale = `<div style="padding:12px; display:flex; flex-direction:column; gap:10px">${stamp(t, { state: 'stale', mobile: true })}<div style="display:flex; gap:8px; align-items:flex-start; padding:10px 12px; border-radius:8px; background:${t.warnBg}; border:1px solid rgba(214,178,94,.35); color:${t.warn}; font-size:13px"><span style="flex:none; margin-top:1px">${ic.alert(16)}</span><span><strong>Dados mais antigos que o esperado.</strong> Os candles deveriam ter sido atualizados há ~7 h (00:05 UTC). O gráfico continua utilizável; os valores podem não refletir o último dia. <a href="#" style="color:${t.warn}; text-decoration:underline">Tentar novamente</a></span></div><div class="hint">Regra: candles/indicadores &gt; 26 h → aviso · resumo 24h &gt; 2 h → aviso. O gráfico não fica bloqueado.</div></div>`;
  const body = `
  <div style="padding:22px 24px 8px"><h1 style="margin:0; text-wrap:balance; font-size:22px; font-weight:700; letter-spacing:-.01em; color:${t.textHi}">Estados do bloco de gráfico</h1><p class="hint" style="margin:4px 0 0">Mesmo container (glass) em todos os estados. Nada muda de lugar. Microcopy exato da spec.</p></div>
  <div style="display:flex; gap:16px; padding:12px 24px; flex-wrap:wrap">
    ${panel('1 · Carregando', 'skeleton no lugar do gráfico; legenda com barras; a toolbar fica ativa', skel)}
    ${panel('2 · Vazio', 'API devolve 200 [] · ativo na lista sem dados recentes', center(ic.layers(24), 'Sem dados para PEPEUSDT em 1h', 'Este ativo está na lista dos top 20, mas ainda não tem candles neste timeframe. Tente outro timeframe ou volte depois da próxima coleta (00:05 UTC).', `<div style="display:flex; gap:8px; margin-top:6px"><button class="btn" style="height:28px">Ver em 1d</button><button class="btn ghost" style="height:28px">Escolher outro ativo</button></div>`))}
    ${panel('3 · Erro', 'API indisponível / 5xx / rede', center(`<span style="color:${t.danger}">${ic.xcircle(24)}</span>`, 'Não foi possível carregar o gráfico', 'A API não respondeu. Tente de novo em alguns segundos.', `<div style="display:flex; gap:8px; margin-top:6px; align-items:center"><button class="btn primary" style="height:28px">${ic.refresh(14)}Tentar novamente</button><span class="hint mono" style="font-size:11px">GET /klines/1h · 503</span></div>`))}
    ${panel('4 · Warm-up parcial', 'linhas começam onde o indicador existe; legenda explica; nunca zero', warm)}
    ${panel('5 · Dados velhos (stale)', 'selo em dourado + alerta inline; o gráfico continua visível', stale)}
    ${panel('6 · Sessão expirada', '401 após refresh falho → redirect para /login?reason=expired', center(ic.clock(24), 'Redirecionando para entrar…', 'Toast discreto: “Sessão expirada. Entre de novo para continuar.” O ativo e o timeframe ficam na URL e são restaurados após o login.'))}
  </div>`;
  return wrap(t, 'Estados', body, { w: W, h: H });
}

// ---------- Sistema ----------
function tokensBoard() {
  const t = T; const W = 1400, H = 1000;
  const sw2 = (name, hex, note = '') => `<div style="display:flex; flex-direction:column; gap:6px; width:118px"><div style="height:46px; border-radius:8px; background:${hex}; border:1px solid ${t.border}"></div><span style="font-size:12px; color:${t.text}">${name}</span><span class="mono" style="font-size:10.5px; color:${t.textMuted}">${hex.startsWith('rgba') ? 'rgba' : hex}${note ? ' · ' + note : ''}</span></div>`;
  const body = `
  <div style="padding:26px 28px; display:flex; flex-direction:column; gap:20px; overflow:hidden">
    <div style="display:flex; align-items:center; gap:14px">${logoImg(44)}<div><h1 style="margin:0; font-size:22px; font-weight:700; color:${t.textHi}">Design system · Dark-Tech</h1><p class="hint" style="margin:2px 0 0">Navy quase preto · glassmorphism · azul elétrico ≤ 20 % da composição · bordas branco-gelo · ciano (da logo) reservado à IA · sem verde, roxo, rosa ou laranja</p></div></div>
    <div><div class="eyebrow" style="margin-bottom:10px">Fundos e vidro</div><div style="display:flex; gap:12px; flex-wrap:wrap">${sw2('bg (navy)', '#060b16')}${sw2('bg profundo', '#04070f')}${sw2('vidro (card)', 'rgba(30,48,80,.42)', 'blur 14')}${sw2('borda gelo', 'rgba(216,230,245,.14)')}${sw2('texto', '#dde6f2')}${sw2('texto muted', '#9fb0c7')}${sw2('texto dim', '#66788f')}</div></div>
    <div><div class="eyebrow" style="margin-bottom:10px">Acentos e dados</div><div style="display:flex; gap:12px; flex-wrap:wrap">${sw2('azul elétrico', '#3e86f7', 'ação/foco')}${sw2('ciano IA', '#5fc4ff', '3ª cor · logo')}${sw2('branco-gelo', '#dbe7f5', 'alta')}${sw2('vermelho', '#e5484d', 'baixa')}${sw2('dourado', '#d6b25e', 'stale')}${sw2('SMA 20', '#4f8ff7')}${sw2('SMA 50', '#2596be')}${sw2('SMA 200', '#c8d9ef')}${sw2('EMA 12', '#8ab8ff', 'tracejada')}${sw2('EMA 26', '#2f5fd0', 'tracejada')}</div></div>
    <div style="display:flex; gap:20px">
      <div class="glass" style="flex:1.2; padding:18px 20px; display:flex; flex-direction:column; gap:12px">
        <div class="eyebrow">Tipografia · Google Sans + Google Sans Code</div>
        <div style="font:700 22px ${SANS}; color:${t.textHi}; letter-spacing:-.02em">Google Sans 700 · títulos</div>
        <div style="font:400 13.5px/1.5 ${SANS}; color:${t.text}">Google Sans 400 · texto de interface, rótulos, mensagens de estado.</div>
        <div class="mono" style="font-size:24px; font-weight:500; color:${t.textHi}">113.512,3 <span style="font-size:13px; color:${t.ice}">▲ +1,84 %</span> <span style="font-size:13px; color:${t.cyan}">previsto 114.890</span></div>
        <div class="mono" style="font-size:13px; color:${t.text}">Google Sans Code · tabular-nums · 19 ago 00:00 UTC · 0,0031 %</div>
        <div class="eyebrow">eyebrow · code 11 · caixa alta · +0.08em</div>
      </div>
      <div style="flex:1; display:flex; flex-direction:column; gap:12px">
        <div class="eyebrow">Controles e superfícies</div>
        <div style="display:flex; gap:10px; align-items:center; flex-wrap:wrap">
          <button class="btn primary">Primário</button><button class="btn">Secundário</button><button class="btn ghost">Ghost</button><span class="chip ai">${ic.sparkle(12)} chip IA</span><span class="chip">chip</span><span class="btn focus">foco visível</span>
        </div>
        <div class="glass" style="padding:14px 16px; display:flex; flex-direction:column; gap:6px">
          <span style="font-weight:700; color:${t.textHi}">Card de vidro</span>
          <span class="hint">fundo translúcido navy · blur 14 px · borda 1 px gelo (14 %) · realce interno 1 px · raio 12</span>
        </div>
        <div class="glass-hi" style="padding:14px 16px; display:flex; flex-direction:column; gap:6px">
          <span style="font-weight:700; color:${t.textHi}">Card destacado (glow)</span>
          <span class="hint">borda gelo 26 % + brilho azul elétrico · uso: no máximo 1 por tela</span>
        </div>
        <div style="display:flex; gap:14px; align-items:center">
          <svg width="130" height="56" viewBox="0 0 130 56" aria-hidden="true"><line x1="12" y1="8" x2="12" y2="48" stroke="${t.ice}"></line><rect x="7" y="16" width="10" height="22" fill="rgba(219,231,245,.10)" stroke="${t.ice}"></rect><line x1="34" y1="4" x2="34" y2="52" stroke="${t.down}"></line><rect x="29" y="12" width="10" height="30" fill="${t.down}"></rect><line x1="62" y1="28" x2="126" y2="8" stroke="${t.ice}" stroke-dasharray="2 3"></line><line x1="62" y1="28" x2="126" y2="24" stroke="${t.cyan}" stroke-width="1.6" stroke-dasharray="5 3"></line><line x1="62" y1="28" x2="126" y2="46" stroke="${t.down}" stroke-dasharray="2 3"></line></svg>
          <span class="hint" style="max-width:34ch">Vela de alta vazada (vidro) · baixa preenchida · cenários: melhor (gelo), esperado (ciano), pior (vermelho)</span>
        </div>
      </div>
    </div>
  </div>`;
  return wrap(t, 'Design system', body, { w: W, h: H });
}

function componentes() {
  const t = T; const W = 1440, H = 1000;
  const box = (title, sub, inner, w = 440) => `<div style="display:flex; flex-direction:column; gap:8px; width:${w}px"><div><div style="font-weight:700; color:${t.textHi}">${title}</div><div class="hint mono" style="font-size:11px">${sub}</div></div><div class="glass" style="padding:14px; display:flex; flex-direction:column; gap:10px; position:relative; min-height:110px">${inner}</div></div>`;
  const body = `
  <div style="padding:22px 24px 8px"><h1 style="margin:0; text-wrap:balance; font-size:22px; font-weight:700; letter-spacing:-.01em; color:${t.textHi}">Inventário de componentes · Nuxt UI v4 (tema Dark-Tech)</h1><p class="hint" style="margin:4px 0 0">Detalhes em docs/design/Design.md e docs/design/components.md</p></div>
  <div style="display:flex; gap:16px; padding:12px 24px; flex-wrap:wrap; align-content:flex-start">
    ${box('InsightCard (Início)', 'componente próprio sobre UCard glass · top-5 com ranking · variante ai com chip', `<div style="display:flex; align-items:center; gap:10px"><span style="width:30px; height:30px; border-radius:8px; background:${t.cyanSoft}; border:1px solid rgba(95,196,255,.35); color:${t.cyan}; display:inline-flex; align-items:center; justify-content:center">${ic.gap(15)}</span><span style="flex:1"><span style="display:block; font-weight:700; color:${t.textHi}; font-size:13px">Maior gap real × projeção</span><span class="hint" style="font-size:11px">linha = ranking + símbolo + valor + delta colorido</span></span><span class="chip ai" style="font-size:10px">IA · v0</span></div>`)}
    ${box('ForecastTable (Previsões)', 'UTable · real + 4 horizontes + confiança · sticky 1ª col · gelo = acima, vermelho = abaixo', `<table class="tbl"><thead><tr><th scope="col">Ativo</th><th scope="col">Real</th><th scope="col">Diária</th></tr></thead><tbody><tr><td translate="no" style="font-weight:500; color:${t.textHi}">ETHUSDT</td><td>4.312,9</td><td><span style="color:${t.ice}">4.511 · +4,6 %</span></td></tr><tr><td translate="no" style="font-weight:500; color:${t.textHi}">XRPUSDT</td><td>3,0120</td><td><span style="color:${t.down}">2,897 · −3,8 %</span></td></tr></tbody></table>`)}
    ${box('AgentSummary', 'UCard glass-hi · texto gerado por agente · links de ativos inline · chip do modelo sempre visível', `<div style="display:flex; gap:10px"><span style="color:${t.cyan}; flex:none">${ic.sparkle(16)}</span><p class="hint" style="margin:0">“O maior descolamento está em <a href="#" translate="no">ETHUSDT</a> (+4,6 %)…” · disclaimer fixo: cenários, não recomendação</p></div>`)}
    ${box('ForecastScenarios (gráfico)', 'LineSeries pós-corte · melhor/esperada/pior · faixa ciano 8 % · toggle no grupo Modelo', `<svg width="200" height="48" viewBox="0 0 200 48" aria-hidden="true"><line x1="10" y1="24" x2="190" y2="8" stroke="${t.ice}" stroke-dasharray="2 3"></line><line x1="10" y1="24" x2="190" y2="22" stroke="${t.cyan}" stroke-width="1.6" stroke-dasharray="5 3"></line><line x1="10" y1="24" x2="190" y2="42" stroke="${t.down}" stroke-dasharray="2 3"></line></svg><span class="hint">rótulos “melhor / esperada / pior” na ponta direita</span>`)}
    ${box('SnapshotStamp', 'UBadge glass · ponto ciano = fresh · dourado = stale · tooltip explica a cadência', `<div style="display:flex; flex-direction:column; gap:8px; align-items:flex-start">${stamp(t)}${stamp(t, { state: 'stale' })}</div>`)}
    ${box('GlassCard / GlowCard', 'UCard com ui.base custom · glow no máximo 1 por tela', `<div style="display:flex; gap:10px"><span class="glass" style="flex:1; padding:10px 12px; font-size:12px">glass</span><span class="glass-hi" style="flex:1; padding:10px 12px; font-size:12px">glass-hi (glow)</span></div>`)}
    ${box('PreferencesForm', 'UForm + USwitch + UCheckboxGroup · canal SMS/WhatsApp com chip Em breve', `<label style="display:flex; justify-content:space-between; align-items:center; gap:12px"><span style="font-size:13px; color:${t.textHi}">Receber notificações</span><span role="switch" tabindex="0" aria-checked="true" style="width:40px; height:24px; border-radius:999px; background:${t.electric}; position:relative; display:inline-block"><i style="position:absolute; top:3px; right:3px; width:18px; height:18px; border-radius:999px; background:#f6f9fd; display:block"></i></span></label><div style="display:flex; gap:6px"><span class="chip" style="border-color:${t.electric}; color:${t.cyan}; background:${t.electricSoft}">E-mail</span><span class="chip" style="opacity:.7">WhatsApp · Em breve</span></div>`)}
    ${box('WelcomeHeader (Início)', 'eyebrow ciano com nome do usuário · h1 · meta do último acesso', `<p class="eyebrow" style="margin:0; color:${t.cyan}">Bem-vindo novamente, Gabriel</p><span style="font-weight:700; color:${t.textHi}; font-size:15px">As principais mudanças desde o seu último acesso</span><span class="hint mono" style="font-size:11px">último acesso 17 ago 22:14 UTC</span>`)}
    ${box('EmptyState / ErrorState', 'sobre glass · ícone 24 · título · texto com próximo passo · retry primário', `<div style="display:flex; gap:8px; align-items:center"><span style="color:${t.danger}">${ic.xcircle(20)}</span><div style="flex:1"><div style="font-weight:700; color:${t.textHi}; font-size:13px">Não foi possível carregar o gráfico</div><div class="hint">A API não respondeu. Tente de novo em alguns segundos.</div></div><button class="btn primary" style="height:28px">${ic.refresh(14)}Tentar novamente</button></div>`)}
    ${box('App shell / nav', 'UHeader + UNavigationMenu · Início · Gráficos · Previsões · Mercado · conta: Preferências/Sair', `<div style="display:flex; gap:4px; flex-wrap:wrap">${[['Início', ic.home(15), false], ['Gráficos', ic.candle(15), true], ['Previsões', ic.sparkle(15), false], ['Mercado', ic.table(15), false]].map(([l, i, a]) => `<span style="display:inline-flex; align-items:center; gap:6px; height:30px; padding:0 10px; border-radius:8px; font-size:12.5px; font-weight:500; color:${a ? t.textHi : t.textMuted}; background:${a ? t.electricSoft : 'transparent'}; ${a ? `border:1px solid rgba(62,134,247,.35)` : ''}">${i}${l}</span>`).join('')}</div><div class="hint">logo com mix-blend-mode:screen sobre o navy · sem toggle de tema (dark-only)</div>`)}
  </div>`;
  return wrap(t, 'Componentes', body, { w: W, h: H });
}

// ---------- escrever ----------
const files = {
  'Main.dc.html': home(),
  'HomeMobile.dc.html': homeMobile(),
  'Login.dc.html': loginSplit(),
  'LoginErro.dc.html': loginSplit('error'),
  'SessaoExpirada.dc.html': loginSplit('expired'),
  'Cadastro.dc.html': authCadastro(),
  'ConfirmeEmail.dc.html': authConfirm(),
  'EsqueciSenha.dc.html': authEsqueci(),
  'RedefinirSenha.dc.html': authRedefinir(),
  'Graficos.dc.html': graficos(),
  'GraficosMobile.dc.html': graficosMobile(),
  'IndicadoresDrawer.dc.html': drawerMobile(),
  'Previsoes.dc.html': previsoes(),
  'Mercado.dc.html': mercado(),
  'MercadoMobile.dc.html': mercadoMobile(),
  'Preferencias.dc.html': preferencias(),
  'Estados.dc.html': estados(),
  'DesignSystem.dc.html': tokensBoard(),
  'Componentes.dc.html': componentes(),
};
for (const [n, c] of Object.entries(files)) writeFileSync(n, c);

const ab = (file, x, y, w, h, page, title) => ({ file, x, y, w, h, page, ...(title ? { title } : {}) });
const canvas = {
  pages: [{ id: 'fluxos', name: 'Fluxos e telas' }, { id: 'sistema', name: 'Design system' }],
  artboards: [
    ab('Login.dc.html', 0, 0, 1440, 900, 'fluxos', 'Login · split'),
    ab('LoginErro.dc.html', 1500, 0, 1440, 900, 'fluxos', 'Login · erro genérico'),
    ab('SessaoExpirada.dc.html', 3000, 0, 1440, 900, 'fluxos', 'Login · sessão expirada'),
    ab('Cadastro.dc.html', 4500, 0, 480, 700, 'fluxos', 'Cadastro'),
    ab('ConfirmeEmail.dc.html', 5040, 0, 480, 640, 'fluxos', 'Verifique seu e-mail'),
    ab('EsqueciSenha.dc.html', 4500, 760, 480, 560, 'fluxos', 'Esqueci a senha'),
    ab('RedefinirSenha.dc.html', 5040, 700, 480, 560, 'fluxos', 'Redefinir senha'),
    ab('Main.dc.html', 0, 1020, 1440, 960, 'fluxos', 'Início · insights pós-login'),
    ab('HomeMobile.dc.html', 1500, 1020, 390, 844, 'fluxos', 'Início · mobile'),
    ab('Graficos.dc.html', 1950, 1020, 1440, 960, 'fluxos', 'Gráficos · candles + cenários IA'),
    ab('GraficosMobile.dc.html', 3450, 1020, 390, 844, 'fluxos', 'Gráficos · mobile'),
    ab('IndicadoresDrawer.dc.html', 3900, 1020, 390, 844, 'fluxos', 'Indicadores · drawer'),
    ab('Previsoes.dc.html', 0, 2100, 1440, 1080, 'fluxos', 'Previsões · tabela + resumo IA'),
    ab('Mercado.dc.html', 1500, 2100, 1440, 900, 'fluxos', 'Mercado · resumo 24h'),
    ab('MercadoMobile.dc.html', 3000, 2100, 390, 844, 'fluxos', 'Mercado · mobile'),
    ab('Preferencias.dc.html', 0, 3300, 1440, 900, 'fluxos', 'Preferências'),
    ab('Estados.dc.html', 1500, 3300, 1440, 900, 'fluxos', 'Estados do gráfico'),
    ab('DesignSystem.dc.html', 0, 0, 1400, 1000, 'sistema', 'Tokens · Dark-Tech'),
    ab('Componentes.dc.html', 1460, 0, 1440, 1000, 'sistema', 'Componentes novos'),
  ],
  annotations: [
    { id: 'nota-v2', x: 0, y: -150, w: 640, text: 'REDESIGN v2 · Dark-Tech: navy #060b16, glass, azul elétrico #3e86f7 (até 20% da composição), bordas gelo, ciano #5fc4ff (da logo) reservado à IA. Dark-only (decisão 19 ago). Alta = vela vazada vidro-gelo; baixa = vermelho. Sem verde, roxo, rosa ou laranja.', page: 'fluxos' },
    { id: 'nota-home', x: 0, y: 960, w: 560, text: 'Nova Home pós-login: “Bem-vindo novamente” + top-5 de volatilidade, gap real×projeção (IA) e volume desde o último acesso. Dados de IA levam chip “IA · v0” até o modelo entrar em produção (marco 3).', page: 'fluxos' },
    { id: 'nota-prev', x: 0, y: 2040, w: 560, text: 'Previsões: tabela top-20 com horizontes diário/semanal/mensal/anual + resumo em texto gerado por agente + Monte Carlo como “Em breve”. Cenários melhor/esperado/pior também no gráfico de candles.', page: 'fluxos' },
    { id: 'nota-v1', x: 0, y: 3240, w: 520, text: 'A versão anterior (Observatório, dark+light, IBM Plex) segue no histórico de versões deste canvas e em docs/design/canvas/ no git.', page: 'fluxos' },
  ],
  launch: { view: 'canvas', page: 'fluxos' },
};
writeFileSync('canvas.json', JSON.stringify(canvas, null, 2));
console.log('ok', Object.keys(files).length, 'artboards');
