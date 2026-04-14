from rest_framework.response import Response
from rest_framework.views import APIView

from open_api.auth import OpenApiKeyAuthentication, OpenApiAnonymousAuthentication


class OpenAPIView(APIView):
    authentication_classes = [OpenApiKeyAuthentication, OpenApiAnonymousAuthentication]

    def success(self, data=None, message='ok'):
        return Response({
            'code': 0,
            'message': message,
            'data': data,
        })

    def created(self, data=None, message='created'):
        return Response({
            'code': 0,
            'message': message,
            'data': data,
        }, status=201)
