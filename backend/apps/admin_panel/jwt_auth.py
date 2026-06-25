import time
import jwt
from functools import wraps
from django.conf import settings
from rest_framework.response import Response


def generate_token(admin_id: int) -> str:
    now = int(time.time())
    return jwt.encode(
        {'sub': str(admin_id), 'iat': now, 'exp': now + 86400},
        settings.SECRET_KEY,
        algorithm='HS256',
    )


def verify_token(token: str) -> dict:
    return jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])


def admin_api_required(method):
    """Decorator for APIView methods. Validates JWT and sets request.admin_id."""
    @wraps(method)
    def wrapper(self, request, *args, **kwargs):
        auth = request.headers.get('Authorization', '')
        if not auth.startswith('Bearer '):
            return Response({'error': 'missing_token'}, status=401)
        try:
            payload = verify_token(auth[7:])
            request.admin_id = payload['sub']
        except jwt.ExpiredSignatureError:
            return Response({'error': 'token_expired'}, status=401)
        except jwt.InvalidTokenError:
            return Response({'error': 'invalid_token'}, status=401)
        return method(self, request, *args, **kwargs)
    return wrapper
