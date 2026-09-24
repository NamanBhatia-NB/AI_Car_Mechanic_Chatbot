"""
Modal Serverless Deployment for Instant Mechanic Django Backend.
Run: `modal deploy backend/deploy_modal.py`
"""

import modal

app = modal.App("instant-mechanic-backend")

# Create a persistent volume for SQLite DB and media uploads
volume = modal.Volume.from_name("mechanic-db-volume", create_if_missing=True)

image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "Django>=5.0,<5.2",
        "djangorestframework>=3.14.0",
        "django-cors-headers>=4.3.0",
        "drf-spectacular>=0.27.0",
        "google-generativeai>=0.8.0",
        "pillow>=10.0.0",
        "python-dotenv>=1.0.0",
        "whitenoise>=6.6.0",
        "gunicorn>=21.2.0"
    )
)

@app.function(
    image=image,
    volumes={"/data": volume},
    secrets=[modal.Secret.from_name("instant-mechanic-secrets")]
)
@modal.wsgi_app()
def wsgi_app():
    import os
    import sys
    from pathlib import Path

    # Set up Django environment
    backend_dir = Path(__file__).resolve().parent
    sys.path.insert(0, str(backend_dir))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mechanic_backend.settings")

    from django.core.wsgi import get_wsgi_application
    return get_wsgi_application()
