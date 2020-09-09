from django.conf import settings


"""Define global attributes for templates"""
def extend(request):
    params = {
        'url_name': request.resolver_match.url_name,
        'site_name': settings.PROJECT_NAME
    }

    return params
