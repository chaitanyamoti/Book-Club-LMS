# Book Club Manager

Quick start README for setting up and running the project locally.

## Requirements

- Python 3.11+ (3.12 used in development)
- Git
- (Optional) PostgreSQL for production

## Setup (Windows)

1. Clone the repo and change directory:
   ```bash
   git clone <repo-url>
   cd bookclub_manager
   ```
2. Create a venv and activate it:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```
3. Upgrade pip and install requirements:
   ```bash
   python -m pip install --upgrade pip setuptools wheel
   pip install -r requirements.txt
   ```

Notes: I replaced `jazzmin==2.5.0` with `django-jazzmin==3.0.1` and replaced `django-qr-code==3.2.0` with `qrcode` to match the codebase.

## Database & Migrations

- The project uses SQLite by default for development.
- Create and apply migrations:
  ```bash
  python manage.py makemigrations
  python manage.py migrate
  ```

## Create Superuser (for admin)

- Non-interactive example (Windows PowerShell / Bash):
  ```bash
  python manage.py createsuperuser --username admin --email admin@example.com --noinput
  python manage.py shell -c "from django.contrib.auth.models import User; u=User.objects.get(username='admin'); u.set_password('AdminPass123'); u.save()"
  ```
- Default credentials created in this environment for testing:
  - **Username:** `admin`
  - **Password:** `AdminPass123`

> Change these credentials before sharing or deploying.

## Running the dev server

```bash
python manage.py runserver
```

Open http://127.0.0.1:8000/ and http://127.0.0.1:8000/admin/ (login with superuser).

## Tests

Run the test suite:

```bash
python manage.py test --verbosity=2
```

I added focused tests for:

- ISBN validation and QR generation (`books/tests.py`)
- Book auto-ISBN and Transaction.is_overdue (`core/tests.py`)
- User signals creating `UserProfile` (`users/tests.py`)
- Notification utilities (`notifications/tests.py`) and dashboard data endpoint (`core/tests.py`)

Run the tests with:

```bash
python manage.py test --verbosity=2
```

## Known issues & debugging tips

- You may see RuntimeWarning about models already registered during repeated `manage.py` invocations; these are harmless in dev but indicate code reloading and should not occur in production.
- If you have problems installing packages, check for correct package names and Python version.
- If you update requirements, run `pip install -r requirements.txt` inside the activated venv.

## Additional notes

- Email backend is configured to console for development (see `bookclub/settings.py`).
- Media files are served from `MEDIA_ROOT` during development.

---

If you'd like, I can commit the migration and test files to a new branch and open a PR, or continue adding tests and CI configuration.

---

## Recent UI/UX Overhaul and Bug Fixes

This project has undergone a significant UI/UX modernization and series of bug fixes.

### Key Improvements:

- **Modernized UI:** The entire dashboard, including the header, sidebar, book list, book request form, and profile page, has been redesigned following modern web design principles (Bootstrap 5, Bootstrap Icons).
- **Improved Navigation:** The old navigation has been replaced with a sticky header and a collapsible sidebar for a cleaner and more intuitive user experience.
- **Redesigned Components:**
  - **Book Cards:** Now feature a modern design with hover effects and clearer information hierarchy.
  - **Profile Page:** Re-implemented with a tabbed layout for better organization of user information and settings.
- **Iconography:** Replaced all Font Awesome icons with Bootstrap Icons for a consistent look and feel.
- **Responsive Design:** Improved responsiveness across various components.

### Bug Fixes:

- **Template Rendering:** Fixed several `TemplateSyntaxError` issues related to unclosed block tags and unregistered custom template tags (`get_item`).
- **URL Routing:** Corrected a `NoReverseMatch` error by pointing the header's search bar to the correct URL.
- **Permissions:** Addressed an issue where normal users could see "Return" buttons, which are intended for staff only. The "Extend" button logic was also clarified to be a user-facing feature.
