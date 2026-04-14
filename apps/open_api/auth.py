from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

from django.core.cache import cache
from django.utils.translation import gettext_lazy as _
from rest_framework.authentication import BaseAuthentication

from application.models import ApplicationApiKey
from common.exception.app_exception import AppAuthenticationFailed
from common.utils.logger import maxkb_logger


@dataclass
class OpenApiTokenDetails:
    token: str
    payload: Optional[Dict[str, Any]] = None


class OpenApiKeyAuthentication(BaseAuthentication):
    keyword = 'Bearer'

    def authenticate(self, request) -> Optional[Tuple[Any, Any]]:
        auth = request.META.get('HTTP_AUTHORIZATION')
        if not auth:
            return None
        if not auth.startswith(f'{self.keyword} '):
            raise AppAuthenticationFailed(1002, _('Authentication information is incorrect! illegal user'))
        token = auth[len(self.keyword) + 1:]
        key = ApplicationApiKey.objects.filter(secret_key=token, is_active=True).select_related('application').first()
        if key is not None:
            return key.application.user or key.application, {'type': 'api_key', 'api_key': key}
        details = OpenApiTokenDetails(token=token, payload=cache.get(f'open_api:{token}'))
        if details.payload is None:
            maxkb_logger.warning('open api token missing or expired')
            raise AppAuthenticationFailed(1003, _('Not logged in, please log in first'))
        user = details.payload.get('user')
        return user, details.payload


class OpenApiAnonymousAuthentication(BaseAuthentication):
    def authenticate(self, request):
        return None
