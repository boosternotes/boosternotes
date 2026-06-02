from .models import NavbarSetting, FooterSetting, StatsSetting


def global_settings(request):
    """
    Injects navbar, footer, stats, and site_settings into every template
    that is rendered via Django's template engine.
    This fixes blank logo/footer on pages that extend index.html
    but don't go through the home() view.
    """
    navbar = NavbarSetting.objects.first()
    footer = FooterSetting.objects.first()
    stats  = StatsSetting.objects.filter(is_active=True).order_by('display_order')

    return {
        'navbar':        navbar,
        'site_settings': navbar,   # alias kept for backward-compat (logo, brand_name etc.)
        'footer':        footer,
        'stats':         stats,
    }
