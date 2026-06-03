from django.core.cache import cache
from .models import NavbarSetting, FooterSetting, StatsSetting


def global_settings(request):
    """
    Injects navbar, footer, stats, and site_settings into every template.
    All queries are cached to avoid hitting the DB on every request.
    Register this in settings.py TEMPLATES > context_processors:
        'myapp.context_processors.global_settings'
    """
    navbar = cache.get('navbar_setting')
    if navbar is None:
        navbar = NavbarSetting.objects.first()
        cache.set('navbar_setting', navbar, 3600)

    footer = cache.get('footer_setting')
    if footer is None:
        footer = FooterSetting.objects.first()
        cache.set('footer_setting', footer, 3600)

    stats = cache.get('stats_setting')
    if stats is None:
        stats = list(StatsSetting.objects.filter(is_active=True).order_by('display_order'))
        cache.set('stats_setting', stats, 3600)

    return {
        'navbar':        navbar,
        'site_settings': navbar,   # alias: used for logo / brand_name in templates
        'footer':        footer,
        'stats':         stats,
    }


# Backward-compat alias
site_settings = global_settings
