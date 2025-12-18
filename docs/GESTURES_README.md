## Gesture Control - Jarvis Mode

This adds real-time hand-gesture control using OpenCV + MediaPipe with app-aware profiles and hot reload.

### Quick Start
1. Install deps:
   ```bash
   python -m pip install -U pip setuptools wheel
   pip install -r Requirements.txt
   ```
2. Run:
   ```bash
   python run_gestures.py
   ```
   - Force a profile: `--profile chrome`
   - Disable reload: `--no-reload`

Press ESC to quit.

### Core Gestures (default)
- open_palm / fist: media play/pause (global)
- pinch: volume mute; pinch_in/out: volume down/up
- swipe_up/down: scroll up/down
- swipe_left/right: media previous/next (global), tab nav in Chrome
- point in Chrome: enter scroll mode (move hand up/down to scroll, fist to exit)
- hold_open_palm (≥1s): Show Desktop
- circle clockwise/ccw: maximize/minimize window

### Profiles & Modes
Config file: `Data/gesture_config.json`.

Schema:
```json
{
  "profiles": {
    "global": { "open_palm": {"type":"keyboard_send","value":"media_play_pause"} },
    "chrome": { "point": {"type":"mode","value":"scroll_mode"} }
  },
  "modes": { "scroll_mode": { "speed": 1.2 } },
  "settings": { "ema_alpha": 0.5, "swipe_threshold_px": 60 }
}
```

Lookup order: `profiles[active_app][gesture]` → `profiles["global"][gesture]`.
Active app detection uses Windows APIs (pywin32); falls back to pygetwindow and title heuristics.

### Tuning Accuracy & Responsiveness
- `settings.ema_alpha` (0–1): smoothing; higher = smoother, slightly less responsive.
- `swipe_threshold_px`: reduce to detect smaller swipes; increase to avoid false positives.
- `pinch_close_px`: distance to consider a pinch closed.
- `pinch_delta_px`: sensitivity for pinch in/out.
- `hold_seconds`: time to trigger hold gestures.
- `cooldown_seconds`: rate limit per gesture.
- `circle_window`: frames to aggregate for circle detection (bigger = more robust, slower).

Adjust these and the app will hot-reload changes while running.

### Action Types
- keyboard_send: send a key name (e.g., `media_play_pause`, `volume_up`).
- keyboard_hotkey: combos like `win+shift+s`, `ctrl+tab`.
- scroll: `{ "amount": ±int }` or via `scroll_mode`.
- move_mouse / click / type_text.
- window: `win_desktop`, `win_switch_win`, `win_minimize`, `win_maximize`.
- chrome: `chrome_new_tab`, `chrome_close_tab`, `chrome_next_tab`, `chrome_prev_tab`.
- mode: enter temporary modes like `scroll_mode`.

### Troubleshooting
- If installation fails on Windows, pin versions (already pinned) and run with Python 3.8–3.12.
- If detection is jittery: increase `ema_alpha`, raise `swipe_threshold_px`, or improve lighting/background.
- If wrong profile is used: ensure the active window is truly focused; try `--profile chrome` to test.
- If MediaPipe can’t access camera: close other apps using the webcam.

### Safety Notes
- Automation sends real keypresses/mouse actions. Save your work before testing new mappings.
- Use cooldowns and holds to prevent accidental triggers.


