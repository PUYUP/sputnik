from django.contrib.auth.decorators import login_required, user_passes_test


consultant_role = user_passes_test(lambda u: True if u.is_consultant else False)
def consultant_required(view_func):
    decorated_view_func = login_required(consultant_role(view_func))
    return decorated_view_func


client_role = user_passes_test(lambda u: True if u.is_client else False)
def client_required(view_func):
    decorated_view_func = login_required(client_role(view_func))
    return decorated_view_func
