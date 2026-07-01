# HermesTranslate UI — translate.html: Requirement Specification & Implementation Plan

> **For:** Junior Developer
> **Status:** Planning Complete — Ready to Implement
> **Date:** 2026-07-01

---

## 1. Goal

สรางหนา translate.html ใหผูใชพมพขอความภาษาไทย ระบบแปลอตโนมตผาน 3 agents (Main -> Translate -> Validate) แสดงผลลพธพรอม progress และ debug info ดวยดไซน 90s Pixel Art

---

## 2. Features

### 2.1 Auto-Translation Flow (Core)

ผใชพมพขอความไทย -> กด "Translate" -> ระบบ chain เรยก 3 agents ผาน `POST /agent/chat`:

| Step | Agent | Input | Output |
|---|---|---|---|
| 1 | Main | Thai text | context_md (markdown) |
| 2 | Translate | context_md | translated text |
| 3 | Validate | translated text | PASS/FAIL + violations |

แสดงผลลพธสดทาย (แปลแลว + validation) ใน result box

### 2.2 Progress Indicator

- Step indicator 3 ขน: `[Main] -> [Translate] -> [Validate]`
- Progress bar แบบ pixel-art (CSS blocks หรอ div width animation)
- แตละขนเปลยนส: pending (gray), running (yellow blinking), done (green), error (red)
- แสดง timing แตละขน (ms) จาก `performance.now()`

### 2.3 Debug Panel

- Terminal-style panel (`<pre>`) แสดง raw output จากแตละ agent
- Meta info: rules_matched, rules_applied, violations, valid
- Timing แตละ agent call (ms)
- Toggle show/hide: ปม `[SHOW DEBUG]` / `[HIDE DEBUG]`
- Color coding: success=green, error=red, info=gray

### 2.4 90s Pixel Art UI

- **Font:** 'Press Start 2P' จาก Google Fonts (`@import`)
- **Color palette (Dark CRT):**
  - `--bg: #0a0a0a`
  - `--text: #33ff33`
  - `--accent: #ffaa00`
  - `--border: #33ff33`
  - `--panel: #111111`
- **CRT scanline effect:** `::after` pseudo-element ทบ `repeating-linear-gradient`
- **Box styling:** border-radius: 0, double-border, box-shadow แบบ pixel steps
- **Button:** sharp corners, pixel border, hover effect (color invert/text glow)
- **Progress bar:** CSS animation, segmented blocks

### 2.5 Light Mode + CRT Theme Toggle

- CSS class `light-mode` บน `<body>`
- **Light palette:** cream bg `#f5f0e1`, dark green text `#1a3a1a`, brown accents `#8b5e3c`
- Toggle switch: pixel-art checkbox hack (`<input type="checkbox">`)
- Transition: `transition: all 0.3s` — เลยนแบบ CRT flicker
- Persist theme ใน `localStorage('hermes-theme')`

### 2.6 Pixel Sprite Animations

- CSS-only pixel character (box-shadow pixel art technique) — ตวละคร 8-bit
- `@keyframes`: `walk` (ขยบขา), `type` (มอขยบ), `celebrate` (กระโดด), `error-shake`
- Animation states: `idle`, `working`, `success`, `error`
- Sprite container แสดงขาง progress bar

### 2.7 Sound Effects (Web Audio API)

| Sound | Frequency | Duration | Type | Trigger |
|---|---|---|---|---|
| Start beep | 440 Hz | 100 ms | square | กด Translate |
| Progress tick | 880 Hz | 50 ms | square | แตละ step เสรจ |
| Success fanfare | C-E-G (ascending) | 300 ms | square | validate PASS |
| Error buzz | 200 Hz | 200 ms | sawtooth | validate FAIL / error |

- ใช `OscillatorNode` + `GainNode` (no external audio files)
- Mute toggle button `[SOUND ON]` / `[SOUND OFF]`
- Persist mute state ใน `localStorage('hermes-sound')`

### 2.8 localStorage History

- เกบผลลพธ 20 รายการลาสดใน `localStorage('hermes-history')`
- Schema: `[{original, translated, status, debug: {timings, meta}, timestamp}]`
- `renderHistory()` — แสดงรายการเปนลสตดานลาง
- `restoreFromHistory(index)` — ใสขอกลบไปใน textarea + แสดงผลเกา
- `clearHistory()` — ลบ `localStorage` + เคลยร DOM
- Load from localStorage on `DOMContentLoaded`

### 2.9 Mobile Responsive

- `<meta name="viewport" content="width=device-width, initial-scale=1.0">`
- max-width 800px container, centered, padding: 16px (mobile) / 32px (desktop)
- `@media (max-width: 768px)`: stack layout (column), font-size เลกลง, full-width buttons
- Touch-friendly: `min-height: 44px; min-width: 44px` บนปมทกปม
- Textarea auto-resize via JS (`this.style.height = 'auto'; this.style.height = this.scrollHeight + 'px'`)

### 2.10 Service Worker — Offline Cache

- **File:** `static/sw.js`
- **Cache name:** `hermes-translate-v1`
- **Precache:** `translate.html`, `nav.html`, Google Fonts CSS URL
- **Strategy:** Cache-first (serve from cache; fetch + update cache in background)
- Register ใน translate.html: `navigator.serviceWorker.register('./sw.js')`
- Offline indicator: แถบดานบน `[OFFLINE MODE]` เมอ `!navigator.onLine`
- Listen `online`/`offline` events

---

## 3. API Endpoints (No Backend Changes)

| Endpoint | Method | Body | Response |
|---|---|---|---|
| `/agent/chat` | POST | `{agent: "main", text: "..."}` | `{agent, input_text, output_text, meta: {rules_matched, rules}}` |
| `/agent/chat` | POST | `{agent: "translate", text: "<context_md>"}` | `{agent, input_text, output_text, meta: {rules_applied, rules}}` |
| `/agent/chat` | POST | `{agent: "validate", text: "<translated>"}` | `{agent, input_text, output_text, meta: {valid, violations}}` |

**Note:** `/agent/chat` เรยก agent โดยตรง (ไมผาน RabbitMQ queue) — ตอบกลบทนท เหมาะสำหรบ interactive UI

---

## 4. File Structure

```
static/
├── nav.html              (EDIT — add <a>Translate</a> link)
├── agents.html           (no change)
├── hermes-manager.html   (no change)
├── translate.html        (CREATE — main deliverable)
└── sw.js                 (CREATE — Service Worker)
```

---

## 5. Design Mockup (ASCII)

```
+--------------------------------------------------+
| [HermesTranslate] [Manager] [Agents] [Translate] |
+--------------------------------------------------+
|                                                    |
|  +----------------------------------------------+  |
|  |  HERMES TRANSLATE              [CRT ON] [=]  |  |
|  +----------------------------------------------+  |
|  |                                              |  |
|  |  > Enter Thai text...                        |  |
|  |  +--------------------------------------+   |  |
|  |  |                                      |   |  |
|  |  |  (textarea)                          |   |  |
|  |  |                                      |   |  |
|  |  +--------------------------------------+   |  |
|  |                                              |  |
|  |  [ TRANSLATE ]  [ CLEAR ]  (=)              |  |
|  |                                              |  |
|  |  PROGRESS                       [sprite]     |  |
|  |  [MAIN done] -> [TRANS working] -> [VAL ...]|  |
|  |  [============--------]                       |  |
|  |                                              |  |
|  |  RESULT                                      |  |
|  |  +--------------------------------------+   |  |
|  |  | Original:                             |   |  |
|  |  | Translated:                           |   |  |
|  |  | Status: PASS (0 violations)           |   |  |
|  |  +--------------------------------------+   |  |
|  |                                              |  |
|  |  [ SHOW DEBUG ]                              |  |
|  |  +--------------------------------------+   |  |
|  |  | $ main     |  23ms | rules: 3        |   |  |
|  |  | $ translate|  45ms | applied: 2      |   |  |
|  |  | $ validate |  12ms | valid: true     |   |  |
|  |  +--------------------------------------+   |  |
|  |                                              |  |
|  |  HISTORY                             [CLEAR] |  |
|  |  [1] -> (PASS)                             |  |
|  |  [2] -> (PASS)                             |  |
|  |                                              |  |
|  +----------------------------------------------+  |
|                                                    |
+--------------------------------------------------+
```

---

## 6. Implementation Plan (14 Tasks)

### Task 1: HTML Structure
**File:** `static/translate.html`
- HTML5 boilerplate + charset + viewport meta
- nav-placeholder div
- Sections: input area, progress bar, result box, debug panel, history list
- Semantic elements: `<header>`, `<main>`, `<section>`

### Task 2: CSS — 90s Pixel Art Dark Theme
**File:** `static/translate.html` (inline `<style>`)
- Import Press Start 2P from Google Fonts (`@import url(...)`)
- CSS custom properties (color palette)
- Body: dark bg, green text, Press Start 2P
- CRT scanline effect: `::after` with `repeating-linear-gradient`
- Box: `border-radius: 0`, double-border, `box-shadow` pixel steps
- Button: sharp corners, pixel border, hover glow

### Task 3: CSS — Light Mode + Theme Toggle
- `body.light-mode` CSS rules: cream bg, dark green text
- Toggle: hidden `<input type="checkbox">` + styled `<label>`
- `transition: all 0.3s`
- JS: toggle class + persist `localStorage('hermes-theme')`

### Task 4: CSS — Responsive + Mobile
- max-width container + centered
- `@media (max-width: 768px)`: column layout, smaller font, full-width buttons
- `min-height: 44px; min-width: 44px` on interactive elements
- Textarea auto-resize JS

### Task 5: CSS — Pixel Sprite Animations
- CSS-only pixel character via `box-shadow` (8x8 or 16x16 grid)
- `@keyframes`: `walk`, `type`, `celebrate`, `error-shake`
- Animation classes: `.sprite-idle`, `.sprite-working`, `.sprite-success`, `.sprite-error`

### Task 6: JS — Auto-Translation Core
- `const API_BASE` fallback (reuse pattern from agents.html)
- `async function autoTranslate(text)`:
  - Step 1: `POST /agent/chat {agent:"main", text}` -> context_md
  - Step 2: `POST /agent/chat {agent:"translate", text: context_md}` -> translated
  - Step 3: `POST /agent/chat {agent:"validate", text: translated}` -> validation
- Error at any step: stop chain, show error, mark remaining steps error

### Task 7: JS — Progress Bar + Timing
- `performance.now()` timestamps per agent call
- Progress bar: update CSS `width` (0% -> 33% -> 66% -> 100%)
- Step indicator: toggle classes `active`, `done`, `error`
- Show timing (ms) below each step label

### Task 8: JS — Debug Panel
- `<pre id="debug-output">` with monospace font
- Toggle button: show/hide panel
- Log per agent: `$ agent_name | XXms | meta_summary`
- Append raw output (truncated to 500 chars if long)
- Color coding via CSS classes: `.debug-success`, `.debug-error`, `.debug-info`

### Task 9: JS — Sound Effects (Web Audio API)
- `playBeep(frequency, duration, type='square')` using `OscillatorNode` + `GainNode`
- Predefined sounds: startBeep, progressTick, successFanfare, errorBuzz
- `AudioContext` created lazily (first user interaction)
- Mute toggle: `localStorage('hermes-sound')`

### Task 10: JS — localStorage History
- `saveToHistory(original, translated, status, debug)` — push + max 20
- `renderHistory()` — list items with click-to-restore
- `restoreFromHistory(index)` — fill textarea + show cached result
- `clearHistory()` — confirm dialog + clear
- Load on `DOMContentLoaded`

### Task 11: JS — Keyboard Shortcuts + UX
- `Ctrl+Enter` -> `autoTranslate()`
- `Escape` -> clear textarea + focus
- Button loading state: disable + "Translating..." text
- Copy result button: `navigator.clipboard.writeText()`

### Task 12: Service Worker
**File:** `static/sw.js`
- `const CACHE_NAME = 'hermes-translate-v1'`
- `self.addEventListener('install', ...)` — precache translate.html, nav.html
- `self.addEventListener('fetch', ...)` — cache-first strategy
- Register in translate.html: `if ('serviceWorker' in navigator) { ... }`
- Offline indicator bar (top of page)

### Task 13: Nav Bar Integration
**File:** `static/nav.html` (DONE — already edited)
- Fetch nav.html + inject into `#nav-placeholder`
- Auto-detect active page from `window.location.pathname`

### Task 14: Testing & Verification
- Open translate.html from disk (`file://`)
- Test: type "xin chao the gioi" -> Translate
- Verify: progress bar runs, steps light up, result shown
- Test: Dark/Light toggle persists across reload
- Test: Sound toggle works
- Test: History save/restore/clear
- Test: Mobile layout (Chrome DevTools > 375px width)
- Test: Offline mode (DevTools > Service Workers)
- Test: Ctrl+Enter, Escape shortcuts
- Test: API down -> graceful error message

---

## 7. Verification Checklist

```
[ ] HTML structure complete (all sections present)
[ ] Press Start 2P font loaded correctly
[ ] CRT scanline effect visible
[ ] Dark/Light theme toggle + persist
[ ] Auto-Translation chain (main -> translate -> validate) works
[ ] Progress bar + step indicator update in real-time
[ ] Debug panel shows timing + meta per agent
[ ] Sound effects play at correct triggers
[ ] Mute toggle works + persist
[ ] History: save, restore, clear
[ ] Mobile responsive (768px breakpoint)
[ ] Service Worker registered + offline cache
[ ] Nav bar shows "Translate" link (active state)
[ ] Ctrl+Enter shortcut works
[ ] Error handling (API down, network error) shows user-friendly message
[ ] Copy result to clipboard works
```

---

## 8. Risks & Edge Cases

| Risk | Mitigation |
|---|---|
| Press Start 2P font slow to load | `font-display: swap` -> fallback to monospace |
| `/agent/chat` takes >5s (LLM latency) | `fetch()` timeout via `AbortController` (30s) + "Still working..." message |
| Service Worker cache stale | Version bump in `CACHE_NAME` + `self.skipWaiting()` |
| Mobile keyboard covers UI | `position: sticky` on textarea + `scrollIntoView()` on focus |
| localStorage full (5MB limit) | `try/catch` + cap at 20 entries |
| Web Audio API blocked (autoplay policy) | Create `AudioContext` on first user click (translate button) |
| `file://` CORS blocks `/agent/chat` | `API_BASE` fallback to `localhost:8000` (existing pattern) |

---

## 9. Dependencies

| Dependency | Source | Reason |
|---|---|---|
| Press Start 2P font | Google Fonts CDN | 90s pixel art typography |
| HermesTranslate API | `localhost:8000` | `/agent/chat` endpoint |
| `static/nav.html` | Existing project file | Shared navigation bar |

**Zero npm/build dependencies** — everything is inline CSS + vanilla JS + CDN font.

---

## 10. Code Patterns to Reuse

From `agents.html`:
```javascript
// API_BASE fallback for file:// protocol
const API_BASE = (window.location.protocol === 'file:' || window.location.origin === 'null')
  ? 'http://localhost:8000'
  : window.location.origin;
```

```javascript
// Nav bar injection
fetch('nav.html').then(r => r.text()).then(h => {
  document.getElementById('nav-placeholder').innerHTML = h;
});
```

```javascript
// Ctrl+Enter shortcut
document.addEventListener('keydown', function(e) {
  if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
    e.preventDefault();
    autoTranslate();
  }
});
```

From `hermes-translate-project` skill:
```javascript
// HTML escaping
function escHtml(s) {
  const d = document.createElement('div');
  d.textContent = s;
  return d.innerHTML;
}
```
