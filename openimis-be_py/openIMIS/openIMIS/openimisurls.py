from django.urls import include, path

from .openimisapps import openimis_apps
from .settings import SITE_ROOT


def openimis_urls():
    return [path('%s%s/' % (SITE_ROOT(), module_name), include('%s.urls' % module_name)) for module_name in openimis_apps()]
