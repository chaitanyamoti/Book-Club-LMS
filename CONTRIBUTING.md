# Contributing to Book Club LMS

Thank you for your interest in contributing to the Book Club LMS project! This guide will help you set up your development environment, understand the project structure, and follow best practices for making contributions.

## 1. Local Development Setup

Please refer to the `README.md` file for detailed instructions on setting up your local development environment, including:
-   Cloning the repository.
-   Setting up a Python virtual environment (`.venv`).
-   Installing dependencies (`requirements.txt`).
-   Running database migrations.
-   Creating a superuser.
-   Running the development server.

## 2. Project Structure (Key Directories)

Here’s an overview of the most important directories and what they contain:

-   `.`: Project root. Contains `manage.py`, `README.md`, `CONTRIBUTING.md`, `.gitignore`, `requirements.txt`, etc.
-   `bookclub/`: Main Django project configuration. Contains `settings.py`, `urls.py`, `wsgi.py`, `asgi.py`.
-   `core/`: Core application containing shared models (`core/models.py`), views (`core/views.py`), URL configurations (`core/urls.py`), context processors, mixins, and custom template tags (`core/templatetags/core_tags.py`).
-   `users/`: User management application. Contains forms for user registration/login, user profile models, and related views.
-   `books/`: Application for managing books. Contains book models, views for listing, adding, editing, and viewing books.
-   `transactions/`: Handles book issue, return, and renewal transactions.
-   `reading/`: Manages reading logs, challenges, and user reading activities.
-   `bookrequests/`: Handles user requests for new books or joining waitlists.
-   `notifications/`: Manages announcements, user notifications, and email logs.
-   `templates/`: Contains all HTML templates, organized by app (e.g., `templates/books/`, `templates/dashboard/`, `templates/includes/`).
    -   `templates/base.html`: The base template for all pages.
    -   `templates/base_dashboard.html`: Extends `base.html` and provides the dashboard-specific layout (header, sidebar, main content area).
    -   `templates/includes/`: Contains reusable HTML snippets like `header.html`, `sidebar.html`, `footer.html`.
-   `static/`: Contains static assets like CSS (`static/css/dashboard.css`), JavaScript, and images (`static/images/`).
-   `media/`: Stores user-uploaded content like book covers and QR codes.

## 3. Git Workflow

We follow a branch-based workflow.

### 3.1. Branching

-   Always create a new branch for your feature, bug fix, or improvement.
-   Name your branches clearly (e.g., `feature/new-dashboard-widget`, `bugfix/login-issue`, `refactor/api-auth`).
-   Avoid working directly on the `main` branch.

```bash
# Update your local main branch
git checkout main
git pull origin main

# Create a new branch
git checkout -b feature/your-feature-name
```

### 3.2. Committing Changes

-   Make frequent, small commits. Each commit should represent a single logical change.
-   Write clear, concise, and descriptive commit messages.
-   Use the imperative mood ("Fix bug," not "Fixed bug").
-   Start the commit message with a type (e.g., `feat:`, `fix:`, `docs:`, `chore:`, `refactor:`).

**Example Commit Message:**
```
feat: Implement user profile editing

This commit adds functionality for users to edit their profile information,
including name, bio, and contact details.

- Implemented `UserProfileUpdateView` in `users/views.py`.
- Created `user_profile_form.html` for profile editing.
- Added URL configuration for the new view.
```

```bash
# Stage your changes
git add .gitignore  # or git add path/to/your/file.py
git add . # to stage all changes in the current directory

# Commit your changes
git commit -m "feat: Concise summary of your change"
# For multi-line messages, create a temporary file and use:
# git commit -F commit_message.txt
```

### 3.3. Pushing Changes

-   Push your branch to GitHub once your changes are ready for review.

```bash
git push origin feature/your-feature-name
```

## 4. Code Style and Quality

-   **Python:** Adhere to PEP 8. Consider using a linter like Black or Flake8.
-   **Django:** Follow Django's best practices for models, views, templates, and forms.
-   **JavaScript:** Use consistent formatting.
-   **HTML/CSS:** Use Bootstrap 5 classes where possible. Maintain responsiveness.

## 5. Running Tests

-   Always run the test suite before submitting your changes to ensure you haven't introduced regressions.

```bash
python manage.py test --verbosity=2
```

## 6. Security Considerations

-   Always consider the security implications of your changes.
-   Ensure proper authentication and authorization checks for sensitive data and actions.
-   Avoid exposing sensitive information.
-   Validate all user input.
