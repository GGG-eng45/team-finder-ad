from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "users"

    def ready(self):
        # import signals to ensure avatar generation on user creation
        try:
            import users.signals  # noqa: F401
        except Exception:
            pass
