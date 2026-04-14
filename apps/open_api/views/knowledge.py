from rest_framework import status

from common.auth.authenticate import AnonymousAuthentication, TokenAuth
from knowledge.models import Knowledge
from open_api.serializers import KnowledgeCreateSerializer, KnowledgeUpdateSerializer
from open_api.services import KnowledgeService
from .base import OpenAPIView


class KnowledgeListView(OpenAPIView):
    authentication_classes = [TokenAuth, AnonymousAuthentication]

    def get(self, request, workspace_id, *args, **kwargs):
        items = KnowledgeService.list_knowledge(workspace_id)
        data = [{
            'id': str(item.id),
            'name': item.name,
            'desc': item.desc,
            'type': item.type,
            'workspace_id': item.workspace_id,
            'create_time': item.create_time,
            'update_time': item.update_time,
        } for item in items]
        return self.success({
            'workspace_id': workspace_id,
            'items': data,
            'page': 1,
            'page_size': len(data),
            'total': len(data),
        })

    def post(self, request, workspace_id, *args, **kwargs):
        serializer = KnowledgeCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        knowledge = KnowledgeService.create_knowledge(workspace_id, user=getattr(request, 'user', None), **serializer.validated_data)
        return self.created({
            'workspace_id': workspace_id,
            'knowledge_id': str(knowledge.id),
            'name': knowledge.name,
        }, message='knowledge created')


class KnowledgeDetailView(OpenAPIView):
    authentication_classes = [TokenAuth, AnonymousAuthentication]

    def get(self, request, workspace_id, knowledge_id, *args, **kwargs):
        knowledge = KnowledgeService.get_knowledge(workspace_id, knowledge_id)
        if knowledge is None:
            return self.success(None, message='knowledge not found')
        return self.success({
            'workspace_id': workspace_id,
            'knowledge_id': str(knowledge.id),
            'name': knowledge.name,
            'desc': knowledge.desc,
            'type': knowledge.type,
            'workspace_id': knowledge.workspace_id,
        })

    def put(self, request, workspace_id, knowledge_id, *args, **kwargs):
        knowledge = KnowledgeService.get_knowledge(workspace_id, knowledge_id)
        if knowledge is None:
            return self.success(None, message='knowledge not found',)
        serializer = KnowledgeUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        for key, value in serializer.validated_data.items():
            setattr(knowledge, key, value)
        knowledge.save(update_fields=list(serializer.validated_data.keys()) + ['update_time'])
        return self.success({
            'workspace_id': workspace_id,
            'knowledge_id': str(knowledge.id),
        }, message='knowledge updated')

    def delete(self, request, workspace_id, knowledge_id, *args, **kwargs):
        count, _ = Knowledge.objects.filter(workspace_id=workspace_id, id=knowledge_id).delete()
        return self.success({
            'workspace_id': workspace_id,
            'knowledge_id': knowledge_id,
            'deleted': count,
        }, message='knowledge deleted')
