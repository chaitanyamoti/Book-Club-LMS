# Demo email settings and working routes

## Email configuration (demo & testing) ✅
- Default (development): console backend (prints emails to the console).
  - Set via environment variable: `EMAIL_BACKEND_TYPE=console` (default)
- File backend (store emails as files, useful for demo):
  - Set `EMAIL_BACKEND_TYPE=file`
  - Optionally set `EMAIL_FILE_PATH` to change folder (default: `<project_root>/sent_emails`).
- SMTP backend (production):
  - Set `EMAIL_BACKEND_TYPE=smtp` and configure `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_USE_TLS`,
    `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`.
- Default from address: `DEFAULT_FROM_EMAIL` (env var or defaults to `Book Club <noreply@bookclub.local>`).

Testing tips:
- For unit tests, use `django.core.mail.backends.locmem.EmailBackend` via `override_settings` so you can inspect sent emails in `django.core.mail.outbox`.


**Where to put real SMTP credentials (for testing/demo)**

- **Recommended**: Put real SMTP credentials in environment variables (or a local `.env` file at the project root). **Never commit** secrets to version control — add your `.env` to `.gitignore`.

- Example `.env` (DO NOT COMMIT):

```
EMAIL_BACKEND_TYPE=smtp
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=you@example.com
EMAIL_HOST_PASSWORD=your-app-or-smtp-password
DEFAULT_FROM_EMAIL="Book Club <noreply@bookclub.com>"
```

- Windows (PowerShell) temporary vars (for a single session):

```
$env:EMAIL_BACKEND_TYPE = 'smtp'
$env:EMAIL_HOST = 'smtp.example.com'
$env:EMAIL_PORT = '587'
$env:EMAIL_USE_TLS = 'True'
$env:EMAIL_HOST_USER = 'you@example.com'
$env:EMAIL_HOST_PASSWORD = 'your-app-or-smtp-password'
```

- Use services intended for testing like **Mailtrap** or **Ethereal** when possible, or create an app-specific password for providers (e.g., Gmail App Passwords).

- For automated tests, prefer `django.core.mail.backends.locmem.EmailBackend` so no real emails are sent.

---

## Working link paths (routes) and front-end templates 📍

Books
- `GET /books/` -> Book list (template: `templates/books/book_list.html`) ✅
- `GET /books/<pk>/` -> Book detail (template: `templates/books/book_detail.html`) ✅
- `GET|POST /books/add/` -> Register a new book (template: `templates/books/book_form.html`) ✅
- `GET|POST /books/edit/<pk>/` -> Edit a book (template: `templates/books/book_form.html`) ✅
- `GET /books/table/` -> Excel-like editable books table (template: `templates/books/book_table.html`) ✅
  - Inline editing saves via `POST /books/table/update/` (JSON payload)
  - CSV export: `GET /books/table/?export=csv`

Transactions
- `GET /transactions/` -> Transactions list (template: `templates/transactions/transaction_list.html`) ✅
- `GET|POST /transactions/issue/` -> Issue a book (template: `templates/transactions/issue_book.html`) ✅
- `GET|POST /transactions/return/<pk>/` -> Return a book (template: `templates/transactions/return_book.html`) ✅

Notifications
- `GET /notifications/` -> Notifications dashboard (template: `templates/notifications/notifications_dashboard.html`) ✅
  - Send Welcome Email (to current user): `POST /notifications/send_welcome/` (available to any logged-in user)
  - Send Overdue Alerts (to all overdue users): `POST /notifications/send_overdue/` (admin/staff only)

Dashboard & others
- Dashboard JSON endpoint: `/dashboard/data/` (used by dashboard; login required)

---

If you'd like, I can: 
1) Add UI permission hints (hide buttons for non-admins) — already added for overdue alerts. ✅
2) Add a small page to view "sent" emails when using file backend. 💡
3) Clean up and consolidate tests to cover the email flows. 🧪

Tell me which next step you prefer.