from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.utils.functional import SimpleLazyObject
from django.contrib.auth import get_user_model

User = get_user_model()


def get_user(request):
    if not hasattr(request, '_cached_user'):
        request._cached_user = get_user_from_token(request)
    return request._cached_user


def get_user_from_token(request):
    try:
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if not auth_header.startswith('Bearer '):
            return AnonymousUser()
        
        token = auth_header.split(' ')[1]
        jwt_auth = JWTAuthentication()
        validated_token = jwt_auth.get_validated_token(token)
        user = jwt_auth.get_user(validated_token)
        return user
    except (InvalidToken, TokenError, IndexError, KeyError):
        return AnonymousUser()


class JWTAuthenticationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Only apply JWT authentication to API requests, not admin or other requests
        if request.path.startswith('/api/'):
            request.user = SimpleLazyObject(lambda: get_user(request))
        # For non-API requests (like admin), let Django handle authentication normally
        return self.get_response(request)
