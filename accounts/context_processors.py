from .models import UserProfile


def user_role(request):
    if not request.user.is_authenticated:
        return {'user_role': None}
    try:
        return {'user_role': request.user.userprofile.role}
    except UserProfile.DoesNotExist:
        return {'user_role': None}

