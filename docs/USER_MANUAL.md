# User Manual — Guinea‑Bissau VFS Booking Helper

This guide walks you through installing, configuring, and using the app to automate VFS Global (Guinea‑Bissau) bookings.

## 1) Quick Start

### Windows (recommended)
1. Double‑click `run_app.bat`
2. The desktop app opens. If prompted, allow camera/microphone if you plan to use Image tab

### Linux/Mac
1. Open a terminal in the project folder
2. `python -m venv .venv`
3. `source .venv/bin/activate`
4. `pip install -r requirements.txt`
5. `playwright install`
6. `python -m app.main`

### Mobile Web App (optional)
1. In another terminal: `python mobile_app.py`
2. On your phone, open `http://<your-computer-ip>:5000`

## 2) App Overview

- URL field: paste the Guinea‑Bissau VFS booking URL
- Options: `Headless` (runs browser in background), `Playwright` (recommended engine)
- Start Bot: begins 3–4 minutes monitoring for slots
- Status light: grey (idle), yellow (working/issues), green (running/ready)
- Tabs: Account, Order, Application, Image, Service, Review & Payment

## 3) Tabs — Step by Step

### 3.1 Account
- Fill: First Name, Last Name, Date of Birth, Email, Password, Confirm Password
- Mobile: pick country code, enter number (digits only are saved)
- Click `Register`:
  - If email exists in `clients.csv`, you’ll see: “This email address already exists.”
  - Otherwise: “Successfully registered.” and data is saved

### 3.2 Order
- Choose: Application Center, Service Center, Trip Reason
- Click `Save`:
  - If the email in Account is set and found in CSV, it updates that record
  - If not found, you’ll see: “Please set the email field in the account tab.”

### 3.3 Application
- Fields: First/Last Name, Gender, Date of Birth, Current Nationality, Passport Number, Passport Expiry, Contact Number, Email
- First/Last Name, Contact Number, Email auto‑fill from Account and are read‑only
- Current Nationality list is populated from country codes file
- Click `Save`:
  - All required fields must be filled (you’ll see validation errors otherwise)
  - If email exists in CSV, record is updated; else a new record is added
  - On success, a confirmation message appears

### 3.4 Image
- `Start Camera`: shows live preview with guidance overlays
- `Capture Photo`: saves image and face detection analysis into `info/`
- Guidance messages (center/size) help comply with passport photo rules
- `Record Video` / `Stop Recording`: optional selfie video capture

### 3.5 Service
- Upload Passport, Photograph, Supporting Documents
- Files are stored under `documents/<sanitized_email>/...`
- Verification checks format, size, and basic quality; results displayed in the panel

### 3.6 Review & Payment
- `Refresh` to generate a consolidated summary from all tabs
- Choose payment method (simulated) and `Process Payment`
- `Confirm Booking` to finalize and save booking confirmation

## 4) Starting the Bot

1. Paste the correct VFS booking URL (Guinea‑Bissau)
2. Options:
   - Headless: ON for real runs (lower detection); OFF for debugging
   - Playwright: ON (recommended); Selenium fallback is automatic if needed
3. Click `Start Bot`
4. The bot monitors for availability within a 3–4 minute window
5. If slots open, it auto‑fills data and submits for up to 5 clients

## 5) Files & Data
- Clients: `clients.csv` (do not edit while bot is running)
- Documents: `documents/<email>/...` (organized by type)
- Images & face data: `info/`
- Logs: `logs/vfs_automation.log`

## 6) FAQ

- Q: Headless vs Playwright?
  - Headless = browser runs without UI, recommended for production
  - Playwright = primary engine with better anti‑bot; keep checked

- Q: URL input — is it used?
  - Yes, the bot navigates to the URL you enter when monitoring starts

- Q: Cloudflare blocks me
  - Use premium proxies in `proxies.txt`
  - Keep Headless ON, reduce request frequency, run during off‑peak

- Q: Duplicate email on Register
  - Use a unique email; the app prevents overwriting existing accounts during registration

- Q: Document upload fails
  - Ensure a valid email is set in Account
  - Use supported types (JPG/PNG/PDF) and sizes

- Q: Where are my photos?
  - Under `info/` with timestamped filenames; face analysis JSON saved alongside

## 7) Troubleshooting

| Problem | Fix |
|---|---|
| `ModuleNotFoundError: PyQt6` | Activate venv and `pip install -r requirements.txt` |
| `403` on VFS | Use different (premium) proxies; enable headless; widen delays |
| Camera not working | Close other camera apps; check OS permissions |
| CAPTCHA unsolved | Integrate 2captcha/anti-captcha in settings (contact admin) |
| Bot never starts | Check URL validity and network connectivity |

## 8) Best Practices
- Keep Headless ON during bookings
- Limit to ≤5 clients per run
- Use high‑quality, residential proxies
- Verify data in Account/Order/Application before starting
- Review the summary before payment

## 9) Support
- Check `logs/vfs_automation.log`
- Review `README.md` and `docs/TECHNICAL_GUIDE.md`
- Share error messages and steps to reproduce when asking for help
