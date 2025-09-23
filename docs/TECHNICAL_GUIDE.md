# Technical Guide — Guinea‑Bissau VFS Booking Helper

## 1) System Overview
- Application type: Desktop GUI (PyQt6) with optional Mobile Web UI (Flask)
- Core function: Monitor VFS Global (Guinea‑Bissau) appointment page ~3–4 minutes and auto‑book up to 5 clients when slots open
- Automation engines: Playwright (primary) + Selenium (fallback)
- Data store: CSV (`clients.csv`) + filesystem for documents/images
- Anti‑bot: Advanced Cloudflare bypass (10 strategies), proxy rotation, stealth fingerprinting, adaptive rate limiting

Directory layout (post‑cleanup):
- `app/`
  - `main.py` — PyQt6 GUI, tabs, worker wiring
  - `services/`
    - `vfs_automation.py` — automation engine, CF bypass, booking flows
    - `csv_io.py` — client CSV I/O, dataclass definitions
    - `country_codes.py` — country calling codes
- `documents/` — uploaded documents per client
  - `_metadata/` — document metadata JSON
- `info/` — captured photos/videos and face detection data
- `templates/` — Flask mobile template(s)
- `static/` — (optional) static assets for mobile UI
- `docs/` — guides and reference
- `tests/` — test utilities
- `logs/` — runtime logs and proxy test reports
- `requirements.txt` — desktop deps
- `mobile_requirements.txt` — mobile app deps
- `run_app.bat`, `run_app.sh` — quick launch scripts
- `proxies.txt` — proxy list (host:port[:user:pass])

## 2) Architecture

### 2.1 GUI (PyQt6)
- `MainWindow` with top controls:
  - URL field, “Headless” and “Playwright” options, Start button, status light
- Tabs:
  - `AccountTab`: registration fields, country code dropdown, CSV save w/ duplicate email check
  - `OrderTab`: Application Center, Service Center, Trip Reason + Save to CSV (by email key)
  - `ApplicationTab`: personal details, autoload from account, read‑only visual separation, validation and CSV upsert
  - `ImageTab`: OpenCV camera preview, face detection (Haar), guidance overlays, capture/record, save to `info/`
  - `ServiceTab`: upload Passport/Photograph/Supporting Docs, organize into `documents/<email>/`, verify type/size/quality
  - `ReviewPaymentTab`: reservation summary, simulated payment, confirmation save
- `VFSBotWorker` (QThread) emits signals: status, availability, progress, booking results

### 2.2 Automation Engine (`VFSAutomation`)
- Start/stop browsers: Playwright context with stealth init scripts; Selenium Chrome fallback
- Cloudflare detection: looks for challenge markers in page content
- Bypass strategies (ordered, retried):
  1) Advanced stealth scripts + fingerprint rotation
  2) Proxy rotation with validation
  3) CAPTCHA solving hook (service integration point)
  4) Browser restart with new fingerprint
  5) Selenium fallback (with stealth)
  6) Basic wait + UA rotation
  7) Enhanced UA rotation + realistic headers
  8) Header spoofing
  9) JavaScript challenge handling
  10) Multi‑browser approach (flip engines)
- Rate limiting: dynamic backoff after errors and CF detection; longer waits once request count rises
- Error handling: consecutive error tracking, automatic restart/recovery, capped retries

### 2.3 Data Layer
- `ClientRecord` dataclass supports all Account/Order/Application fields
- CSV is the single source of truth keyed by `email`
- Filesystem layout:
  - `documents/<email_sanitized>/...`
  - `info/` for images/videos and `face_detection_*.json`
  - `logs/vfs_automation.log` (configure in automation module)

## 3) Environment & Dependencies

### 3.1 Python & Virtualenv
- Python 3.9+ recommended
- Create venv: `python -m venv .venv`
- Activate: Windows `.\.venv\Scripts\activate` | Linux/Mac `source .venv/bin/activate`

### 3.2 Install Deps
- Desktop: `pip install -r requirements.txt`
- Mobile: `pip install -r mobile_requirements.txt`
- Playwright browsers: `playwright install`

### 3.3 Proxy Configuration
- Edit `proxies.txt`, one per line: `host:port[:username:password]`
- Validate: `python tests/test_proxy_validation.py` or `python scripts/find_working_proxies.py`

## 4) Build & Run

### 4.1 Desktop App
- Quick start: `run_app.bat` (Windows) or `./run_app.sh`
- Manual: `.\.venv\Scripts\python -m app.main`

### 4.2 Mobile App
- Run: `python mobile_app.py` (from project root)
- Access: `http://localhost:5000` on the same machine or LAN
- Auto‑launcher: `python scripts/launch_mobile.py`

## 5) Operations — Automation Tuning

- Headless: enable for lower detection probability, disable during debugging
- Engine: prefer Playwright; allow Selenium fallback when needed
- Monitoring window: default ~4 minutes; adjust in GUI or code
- Max clients per session: up to 5; keep < 5 to avoid bans
- Randomized delays: keep ranges wide enough (2–12s bursts + backoff) to mimic humans
- Proxy rotation cadence: rotate on CF detection or hard errors; test proxies periodically

## 6) Cloudflare Bypass — Integration Notes

- Stealth scripts injected cautiously (avoid redefining `navigator.webdriver` twice)
- Headers and UA spoofing kept realistic, with `sec-ch-ua*` and `Accept*`
- CAPTCHA solving: implement token exchange in `_solve_captcha()` (2Captcha/Anti‑captcha) and wire into strategy 3
- Fingerprint rotation changes viewport, WebGL, languages, hardware concurrency, and date/time offsets

## 7) Data & File Handling

- CSV Constraints: unique `email`; `save_clients()` overwrites existing values on update
- File validation: mime/type check, size thresholds, basic image quality checks
- Naming: timestamps added to avoid collisions; email sanitized into folder name

## 8) Logging & Telemetry
- File logger in `logs/vfs_automation.log` + console logging
- Status/Progress signals surfaced to GUI and Mobile UI
- Persist booking results to JSON when successful

## 9) Testing
- Smoke: `tests/test_simple_vfs.py`
- Bypass: `tests/test_enhanced_cloudflare_bypass.py`
- Real session dry‑run: `tests/test_real_vfs_session.py` (requires credentials/network)
- Final system: `tests/test_final_system.py`

## 10) Deployment & Packaging
- Windows: use `pyinstaller` (one‑file or one‑dir) for `app/main.py`
- Include `requirements.txt`, `proxies.txt`, `templates/`, `static/`
- Configure `.env` for API keys (e.g., CAPTCHA) — never hardcode secrets

## 11) Security & Compliance
- Do not store plaintext passwords in CSV for production — prefer encrypted or hashed at rest
- Follow VFS Global ToS; obtain user consent for automation
- Keep proxy credentials secured; restrict logs from leaking sensitive data

## 12) Troubleshooting

| Symptom | Likely Cause | Fix |
|---|---|---|
| `ModuleNotFoundError: PyQt6` | Not in venv | Activate venv, `pip install -r requirements.txt` |
| CF challenge never clears | Bad proxies / aggressive timing | Use premium proxies, widen delays, enable headless |
| `Cannot redefine property: webdriver` | Double define in JS | Use guarded define, only if missing |
| 403 on VFS only | Network/reputation issues | Switch city/ASN proxies; run non‑headless once |
| Crashes after N attempts | Consecutive error cap | Let it recover; check logs; reduce concurrency |

## 13) Extensibility Roadmap
- Plug actual CAPTCHA solver into `_solve_captcha()`
- Persist data to SQLite or a small API instead of CSV
- Add multiple application center profiles per client
- Improve document OCR/validation pipeline
