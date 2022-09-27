from django.conf import settings
from apps.person.utils.constants import CLIENT, CONSULTANT


"""Define global attributes for templates"""
def extend(request):
    params = {
        'url_name': request.resolver_match.url_name,
        'app_name': settings.APP_NAME,
        'api_version': settings.API_VERSION_SLUG,
        'app_version': settings.APP_VERSION_SLUG,
        'role_client': CLIENT,
        'role_consultant': CONSULTANT,
    }

    return params
