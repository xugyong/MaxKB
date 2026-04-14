from django.core.cache import cache

from open_api.serializers import ApiKeyCreateSerializer, ApiKeyUpdateSerializer
from open_api.services import ApiKeyService
from .base import OpenAPIView


class TokenView(OpenAPIView):
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        return self.success({
            'access_token': '',
            'token_type': 'Bearer',
            'expires_in': 0,
        }, message='token endpoint stub')


class MeView(OpenAPIView):
    def get(self, request, *args, **kwargs):
        return self.success({
            'id': getattr(request.user, 'id', None),
            'username': getattr(request.user, 'username', ''),
            'email': getattr(request.user, 'email', ''),
        })


class ApiKeyListView(OpenAPIView):
    def get(self, request, application_id, *args, **kwargs):
        items = ApiKeyService.list_api_keys(application_id)
        return self.success({
            'items': [{
                'id': str(item.id),
                'application_id': str(item.application_id),
                'secret_key': item.secret_key,
                'is_active': item.is_active,
                'allow_cross_domain': item.allow_cross_domain,
                'cross_domain_list': item.cross_domain_list,
                'expire_time': item.expire_time,
                'is_permanent': item.is_permanent,
            } for item in items],
            'total': items.count(),
        })

    def post(self, request, workspace_id, application_id, *args, **kwargs):
        serializer = ApiKeyCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        api_key = ApiKeyService.create_api_key(application_id, workspace_id, **serializer.validated_data)
        return self.created({
            'id': str(api_key.id),
            'application_id': str(api_key.application_id),
            'secret_key': api_key.secret_key,
        }, message='api key created')


class ApiKeyDetailView(OpenAPIView):
    def patch(self, request, workspace_id, application_id, api_key_id, *args, **kwargs):
        serializer = ApiKeyUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        from application.models import ApplicationApiKey
        api_key = ApplicationApiKey.objects.filter(id=api_key_id, application_id=application_id).first()
        if api_key is None:
            return self.success(None, message='api key not found')
        api_key = ApiKeyService.update_api_key(api_key, **serializer.validated_data)
        return self.success({
            'id': str(api_key.id),
            'is_active': api_key.is_active,
        }, message='api key updated')

    def delete(self, request, workspace_id, application_id, api_key_id, *args, **kwargs):
        from application.models import ApplicationApiKey
        api_key = ApplicationApiKey.objects.filter(id=api_key_id, application_id=application_id).first()
        if api_key is None:
            return self.success(None, message='api key not found')
        deleted = ApiKeyService.delete_api_key(api_key)
        return self.success({'deleted': deleted}, message='api key deleted')
