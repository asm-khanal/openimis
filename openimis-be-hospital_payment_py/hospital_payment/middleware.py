"""
Demo authentication middleware for hackathon.
Auto-authenticates all requests as an admin superuser, bypassing login.
ONLY for development/demo use - never use in production.
"""
import logging

from django.contrib.auth.models import AnonymousUser

logger = logging.getLogger(__name__)


class DemoAuthenticationMiddleware:
    """
    Middleware that auto-authenticates all requests as a superuser.
    This eliminates the need for login during hackathon demos.

    Set DEMO_NO_AUTH=True in .env to enable.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        from django.conf import settings

        if getattr(settings, "DEMO_NO_AUTH", False):
            # Only auto-authenticate if no user is already set
            if not hasattr(request, "user") or isinstance(request.user, AnonymousUser):
                from core.models import InteractiveUser, User
                from django.db import connection

                try:
                    # Try to get or create a demo admin user
                    i_user = InteractiveUser.objects.filter(
                        username="admin", validity_to__isnull=True
                    ).first()

                    if not i_user:
                        i_user = InteractiveUser.objects.create(
                            username="admin",
                            other_names="Demo",
                            last_name="Admin",
                            email="admin@demo.local",
                            phone="",
                            language="en",
                            health_facility_id=None,
                            audit_user_id=-1,
                            validity_from=timezone.now(),
                        )

                    # Get or create the Django User wrapper
                    user = User.objects.filter(i_user=i_user).first()
                    if not user:
                        user = User.objects.create_superuser(
                            username="admin",
                            password="admin",
                            i_user=i_user,
                        )

                    request.user = user

                except Exception as e:
                    logger.warning(f"DemoAuth: Could not auto-authenticate: {e}")

        response = self.get_response(request)
        return response


# Need this import at the bottom to avoid circular imports
from django.utils import timezone  # noqa: E402
