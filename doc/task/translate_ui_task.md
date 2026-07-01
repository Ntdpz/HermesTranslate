# HermesTranslate UI — translate.html: Task Checklist

> **For:** Junior Developer
> **Artifact:** `static/translate.html` + `static/sw.js`
> **Total Tasks:** 14 | **Est. Time:** 2-3 hours

---

## Task Status

### Phase: UI Implementation

- [x] **Task 1: HTML Structure**
  - Create `static/translate.html`
  - HTML5 boilerplate, charset, viewport meta
  - nav-placeholder div
  - Sections: input, progress, result, debug, history

- [x] **Task 2: CSS — 90s Pixel Art Dark Theme**
  - Import Press Start 2P font
  - CSS custom properties (dark palette)
  - CRT scanline effect
  - Pixel-art box styling + buttons

- [x] **Task 3: CSS — Light Mode + Theme Toggle**
  - `body.light-mode` rules
  - Toggle checkbox + label
  - localStorage persistence

- [x] **Task 4: CSS — Responsive + Mobile**
  - max-width container
  - @media (max-width: 768px) rules
  - Touch-friendly sizing (44px min)
  - Textarea auto-resize

- [x] **Task 5: CSS — Pixel Sprite Animations**
  - Box-shadow pixel character
  - @keyframes: walk, type, celebrate, error-shake
  - Animation state classes

### Phase: JavaScript Logic

- [x] **Task 6: JS — Auto-Translation Core**
  - API_BASE fallback
  - Chain: main -> translate -> validate via `/agent/chat`
  - Error handling per step

- [x] **Task 7: JS — Progress Bar + Timing**
  - performance.now() timestamps
  - Progress bar width updates
  - Step indicator state classes

- [x] **Task 8: JS — Debug Panel**
  - `<pre>` output element
  - Toggle show/hide button
  - Per-agent log: name, timing, meta
  - Color coding

- [x] **Task 9: JS — Sound Effects (Web Audio API)**
  - playBeep() with OscillatorNode
  - Predefined: start, tick, success, error
  - Mute toggle + localStorage

- [x] **Task 10: JS — localStorage History**
  - save/restore/clear history
  - Max 20 entries
  - Click-to-restore in list

- [x] **Task 11: JS — Keyboard Shortcuts + UX**
  - Ctrl+Enter -> translate
  - Escape -> clear
  - Loading state (disable button)
  - Copy result button

### Phase: Infrastructure

- [x] **Task 12: Service Worker**
  - Create `static/sw.js`
  - Cache-first strategy
  - Register in translate.html
  - Offline indicator

- [x] **Task 13: Nav Bar Integration**
  - Fetch nav.html inject pattern (DONE — nav.html already updated with Translate link)
  - Active page auto-detection

### Phase: Verification

- [x] **Task 14: Testing & Verification**
  - Open from disk (file://)
  - Test full flow: type -> translate -> result
  - Test Dark/Light toggle
  - Test sound toggle
  - Test history
  - Test mobile layout
  - Test offline mode
  - Test keyboard shortcuts
  - Test error handling (API down)
