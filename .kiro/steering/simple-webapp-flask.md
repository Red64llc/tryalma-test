# Simple Flask Web Application Patterns

Lightweight Flask web applications with blueprints, Jinja2 templating, and simple data handling. For REST APIs, prefer FastAPI (see `python-fast-api.md`).

---

## When to Use Flask

Choose Flask for:
- Simple web UIs with server-rendered templates
- Admin dashboards
- Internal tools
- Quick prototypes
- Small applications where FastAPI's async is overkill

Choose FastAPI for:
- REST/JSON APIs (see `python-fast-api.md`)
- High-performance async requirements
- OpenAPI documentation needs

---

## Application Factory Pattern

Always use the application factory pattern for testability and flexibility.

```python
# app/__init__.py
from flask import Flask

def create_app(config_name: str = "default") -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__)

    # Load configuration
    app.config.from_object(config[config_name])

    # Register blueprints
    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix="/auth")

    # Register error handlers
    register_error_handlers(app)

    return app
```

---

## Project Structure

```
app/
  __init__.py          # Application factory
  config.py            # Configuration classes
  extensions.py        # Flask extensions (db, login, etc.)
  models.py            # SQLAlchemy models (if using)
  main/
    __init__.py        # Blueprint definition
    routes.py          # Route handlers
    forms.py           # WTForms (if using)
  auth/
    __init__.py
    routes.py
  templates/
    base.html          # Base template
    main/
      index.html
    auth/
      login.html
  static/
    css/
    js/
```

### Layer Responsibilities

| Layer | Purpose |
|-------|---------|
| **Routes** | Handle HTTP, delegate to services |
| **Forms** | Validate user input (WTForms) |
| **Templates** | Render HTML responses |
| **Models** | Database entities |

---

## Blueprint Pattern

Each feature module uses a Blueprint for organization.

```python
# app/main/__init__.py
from flask import Blueprint

bp = Blueprint("main", __name__)

from app.main import routes  # noqa: E402,F401
```

```python
# app/main/routes.py
from flask import render_template, request, redirect, url_for, flash
from app.main import bp

@bp.route("/")
def index():
    """Home page."""
    return render_template("main/index.html")

@bp.route("/dashboard")
def dashboard():
    """Dashboard view."""
    items = get_dashboard_items()
    return render_template("main/dashboard.html", items=items)
```

---

## Configuration Pattern

Use class-based configuration with environment overrides.

```python
# app/config.py
import os

class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-key-change-me")
    DEBUG = False
    TESTING = False

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True

class ProductionConfig(Config):
    """Production configuration."""
    SECRET_KEY = os.environ["SECRET_KEY"]  # Required in production

class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True

config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}
```

---

## Template Patterns

### Base Template

```html
<!-- templates/base.html -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{% block title %}App{% endblock %}</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
</head>
<body>
    <nav>{% include 'partials/nav.html' %}</nav>

    <main>
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% for category, message in messages %}
                <div class="alert alert-{{ category }}">{{ message }}</div>
            {% endfor %}
        {% endwith %}

        {% block content %}{% endblock %}
    </main>

    {% block scripts %}{% endblock %}
</body>
</html>
```

### Page Template

```html
<!-- templates/main/dashboard.html -->
{% extends "base.html" %}

{% block title %}Dashboard{% endblock %}

{% block content %}
<h1>Dashboard</h1>
<ul>
    {% for item in items %}
        <li>{{ item.name }}</li>
    {% else %}
        <li>No items found.</li>
    {% endfor %}
</ul>
{% endblock %}
```

---

## Form Handling

### Without WTForms (Simple)

```python
@bp.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()

        errors = []
        if not name:
            errors.append("Name is required")
        if not email or "@" not in email:
            errors.append("Valid email is required")

        if errors:
            for error in errors:
                flash(error, "error")
            return render_template("main/contact.html", name=name, email=email)

        # Process form
        send_contact_email(name, email)
        flash("Message sent!", "success")
        return redirect(url_for("main.index"))

    return render_template("main/contact.html")
```

### With WTForms (Recommended for Complex Forms)

```python
# app/main/forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField
from wtforms.validators import DataRequired, Email

class ContactForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email()])
    message = TextAreaField("Message", validators=[DataRequired()])
```

```python
# app/main/routes.py
@bp.route("/contact", methods=["GET", "POST"])
def contact():
    form = ContactForm()
    if form.validate_on_submit():
        send_contact_email(form.name.data, form.email.data, form.message.data)
        flash("Message sent!", "success")
        return redirect(url_for("main.index"))
    return render_template("main/contact.html", form=form)
```

---

## Error Handling

```python
# app/__init__.py
def register_error_handlers(app: Flask) -> None:
    """Register custom error handlers."""

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def internal_error(error):
        return render_template("errors/500.html"), 500
```

---

## Testing

```python
# tests/conftest.py
import pytest
from app import create_app

@pytest.fixture
def app():
    """Create application for testing."""
    app = create_app("testing")
    yield app

@pytest.fixture
def client(app):
    """Test client."""
    return app.test_client()

# tests/test_main.py
def test_index_returns_200(client):
    response = client.get("/")
    assert response.status_code == 200

def test_contact_post_validates_email(client):
    response = client.post("/contact", data={"name": "Test", "email": "invalid"})
    assert b"Valid email" in response.data
```

---

## Running the Application

```python
# run.py or wsgi.py
from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run()
```

```bash
# Development
flask --app app run --debug

# Production (use Gunicorn)
gunicorn -w 4 "app:create_app()"
```

---

## Anti-Patterns to Avoid

### 1. Circular Imports

```python
# Bad: Import app at module level
from app import app  # Circular!

# Good: Use blueprints and current_app
from flask import current_app, Blueprint
bp = Blueprint("main", __name__)
```

### 2. Logic in Templates

```html
<!-- Bad: Business logic in template -->
{% if user.created_at|days_since > 30 and user.orders|length > 5 %}
    Premium User
{% endif %}

<!-- Good: Compute in view, pass result -->
{% if is_premium_user %}
    Premium User
{% endif %}
```

### 3. Hardcoded URLs

```python
# Bad
return redirect("/dashboard")

# Good
return redirect(url_for("main.dashboard"))
```

---

_This steering covers simple Flask patterns. For REST APIs, use FastAPI instead._
