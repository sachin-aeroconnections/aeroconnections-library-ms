from django.core.cache import cache

_BRANDING_CACHE_KEY = "branding_context"
_BRANDING_CACHE_TIMEOUT = 300  # 5 minutes


def branding_context(request):
    cached = cache.get(_BRANDING_CACHE_KEY)
    if cached is not None:
        return {"branding": cached}

    from apps.notifications.models import Branding
    branding = Branding.get_active()

    if branding:
        data = {
            'company_name': branding.company_name,
            'library_name': branding.library_name,
            'logo_url': branding.logo.url if branding.logo else '/static/logo.png',
            'show_company_name': branding.show_company_name,
            'show_library_name': branding.show_library_name,
            'logo_invert': branding.logo_invert,
            'primary_color': branding.primary_color,
            'secondary_color': branding.secondary_color,
            'accent_color': branding.accent_color,
        }
    else:
        from django.conf import settings
        data = {
            'company_name': getattr(settings, 'COMPANY_NAME', 'AeroConnections'),
            'library_name': getattr(settings, 'LIBRARY_NAME', 'Library Management System'),
            'logo_url': getattr(settings, 'LOGO_URL', '/static/logo.png'),
            'show_company_name': True,
            'show_library_name': True,
            'logo_invert': True,
            'primary_color': getattr(settings, 'PRIMARY_COLOR', '#DA291C'),
            'secondary_color': getattr(settings, 'SECONDARY_COLOR', '#5B6770'),
            'accent_color': getattr(settings, 'ACCENT_COLOR', '#C8C9C7'),
        }

    cache.set(_BRANDING_CACHE_KEY, data, _BRANDING_CACHE_TIMEOUT)
    return {"branding": data}
