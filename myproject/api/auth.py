from django.http import HttpRequest
from ninja.security import HttpBearer
from ninja_jwt.authentication import JWTBaseAuthentication


class CookieJWTAuth(JWTBaseAuthentication, HttpBearer):
    def authenticate(self, request: HttpRequest, token: str = None):
        raw = request.COOKIES.get("access_token")
        if not raw:
            return None
        return self.jwt_authenticate(request, raw)