from .models import NavbarSetting, FooterSetting, StatsSetting


def global_settings(request):
    """
    Injects navbar, footer, stats, and site_settings into every template.
    Register this in settings.py TEMPLATES > context_processors:
        'myapp.context_processors.global_settings'
    """
    navbar = NavbarSetting.objects.first()
    footer = FooterSetting.objects.first()
    stats  = StatsSetting.objects.filter(is_active=True).order_by('display_order')

    return {
        'navbar':        navbar,
        'site_settings': navbar,   # alias: used for logo / brand_name in templates
        'footer':        footer,
        'stats':         stats,
    }


# Backward-compat alias — in case settings.py still references the old name
site_settings = global_settings
