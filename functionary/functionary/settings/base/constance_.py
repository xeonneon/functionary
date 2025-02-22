CONSTANCE_BACKEND = "constance.backends.database.DatabaseBackend"
CONSTANCE_DATABASE_PREFIX = "constance:functionary:"
CONSTANCE_ADDITIONAL_FIELDS = {
    "config_field": ["django.forms.fields.JSONField", {}],
}
CONSTANCE_CONFIG = {
    "SOCIALACCOUNT_PROVIDERS": (
        {
            "github": {},
            "gitlab": {},
            "keycloak": {},
        },
        "SocialAccount Providers Configuration",
        "config_field",
    ),
    "S3_HOST": ("", "Server Hostname", str),
    "S3_PORT": (9000, "Port", int),
    "S3_REGION": ("", "Region", str),
    "S3_ACCESS_KEY": ("", "Access Key", str),
    "S3_SECRET_KEY": ("", "Secret Key", str),
    "S3_SECURE": (False, "Require Secure Access", bool),
    "S3_PRESIGNED_URL_TIMEOUT_MINUTES": (5, "Download URL Timeout (minutes)", int),
}
CONSTANCE_CONFIG_FIELDSETS = {
    "S3 Settings": {
        "fields": (
            "S3_HOST",
            "S3_PORT",
            "S3_REGION",
            "S3_SECURE",
            "S3_ACCESS_KEY",
            "S3_SECRET_KEY",
            "S3_PRESIGNED_URL_TIMEOUT_MINUTES",
        )
    },
    "HIDDEN": {"fields": ("SOCIALACCOUNT_PROVIDERS",)},
}


def constance_settings_proxy(setting_name, default_value):
    """Custom settings function for django-allauth.

    This function will check Constance for the given setting_name and
    revert to the django.conf.settings if it's not found. This function
    allows the SOCIALACCOUNT_PROVIDERS to be configured outside of these
    config files.

    Args:
        setting_name: The name of the setting to fetch
        default_value: The default to use if it's not configured

    Returns:
        The configured setting from Constance. If it's not found, the setting
        from django.conf.settings, otherwise the default_value.
    """
    import json

    from constance import config
    from django.conf import settings

    value = getattr(config, setting_name, None)
    if value is None:
        return getattr(settings, setting_name, default_value)
    try:
        return json.loads(value)
    except Exception:
        return value
