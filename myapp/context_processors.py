# app/context_processors.py

from .models import NavbarSetting

def site_settings(request):
    settings = NavbarSetting.objects.first()

    return {
        'site_settings': settings
    }