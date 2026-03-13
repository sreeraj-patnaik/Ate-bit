# OpportunityHub

Full-stack Django + SQLite app for organizing internship, job, and hackathon opportunities.

## Setup

1. Activate virtual environment:
   - PowerShell: `.\\.venv\\Scripts\\Activate.ps1`
2. Add your Groq key:
   - Copy `.env.example` to `.env` (already created)
   - Set `GROQ_API_KEY=...`
3. Run migrations:
   - `python manage.py migrate`
4. Start server:
   - `python manage.py runserver`
   - For mobile LAN access: `python manage.py runserver 0.0.0.0:8000`

## LLM Integration

- Main integration file: `services/llm_interface.py`
- If `GROQ_API_KEY` is available, it uses Groq chat completion.
- If not, it falls back to regex/mock extraction.

## OCR Input (Screenshots)

- Submit page now supports image upload OCR in addition to pasted text.
- OCR service file: `services/ocr_service.py`
- Required Python deps: `Pillow`, `pytesseract`
- System dependency:
  - Install Tesseract OCR engine on your machine.
  - On Windows, set `TESSERACT_CMD` in `.env` if not auto-detected.
  - Example: `TESSERACT_CMD=C:\\Program Files\\Tesseract-OCR\\tesseract.exe`

## Mobile API (JWT)

Base path: `/api`

- `POST /api/auth/register`
- `POST /api/auth/token`
- `POST /api/auth/token/refresh`
- `GET/PUT /api/profile`
- `GET/POST /api/opportunities`
- `POST /api/opportunities/extract`
- `GET/PUT/DELETE /api/opportunities/{id}`
- `POST /api/opportunities/{id}/notes`
- `GET /api/timeline`
- `POST /api/devices` (register mobile push token)

## Notifications

Implemented channels:
- Email (uses Django email backend)
- Mobile push (Firebase Admin SDK, requires service account)

Triggers:
- Immediate when message is scanned
- 7 days before deadline
- 3 days before deadline
- 1 day before deadline

Run scheduled reminders manually:
- `python manage.py send_deadline_notifications`

Automate by running this command daily with Windows Task Scheduler or cron.
