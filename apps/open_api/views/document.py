from open_api.serializers import DocumentUploadSerializer
from open_api.services import KnowledgeService, DocumentService
from knowledge.models import Document
from .base import OpenAPIView


class DocumentListView(OpenAPIView):
    def get(self, request, workspace_id, knowledge_id, *args, **kwargs):
        knowledge = KnowledgeService.get_knowledge(workspace_id, knowledge_id)
        if knowledge is None:
            return self.success(None, message='knowledge not found')
        items = DocumentService.list_documents(knowledge)
        data = [{
            'id': str(item.id),
            'knowledge_id': str(item.knowledge_id),
            'name': item.name,
            'status': item.status,
            'status_meta': item.status_meta,
            'type': item.type,
            'create_time': item.create_time,
            'update_time': item.update_time,
        } for item in items]
        return self.success({
            'workspace_id': workspace_id,
            'knowledge_id': knowledge_id,
            'items': data,
            'page': 1,
            'page_size': len(data),
            'total': len(data),
        })

    def post(self, request, workspace_id, knowledge_id, *args, **kwargs):
        knowledge = KnowledgeService.get_knowledge(workspace_id, knowledge_id)
        if knowledge is None:
            return self.success(None, message='knowledge not found')
        serializer = DocumentUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        name = serializer.validated_data.get('name')
        uploaded = serializer.validated_data.get('file')
        text = serializer.validated_data.get('text') or ''
        if not name:
            name = getattr(uploaded, 'name', '') if uploaded is not None else ''
        if not name:
            name = 'document'
        if text:
            document_id = DocumentService.create_from_text(workspace_id, knowledge, name, text, user=getattr(request, 'user', None))
            return self.created({
                'workspace_id': workspace_id,
                'knowledge_id': knowledge_id,
                'document_id': str(document_id),
                'status': 'processing',
                'status_meta': {'state_time': {}},
            }, message='document uploaded')
        if uploaded is not None:
            document_id = DocumentService.create_from_file(workspace_id, knowledge, uploaded, name=name)
            return self.created({
                'workspace_id': workspace_id,
                'knowledge_id': knowledge_id,
                'document_id': str(document_id),
                'status': 'processing',
                'status_meta': {'state_time': {}},
            }, message='document uploaded')
        document = Document.objects.create(
            knowledge=knowledge,
            name=name,
            char_length=0,
            type=knowledge.type,
            meta={},
        )
        return self.created({
            'workspace_id': workspace_id,
            'knowledge_id': knowledge_id,
            'document_id': str(document.id),
            'status': document.status,
            'status_meta': document.status_meta,
        }, message='document uploaded')


class DocumentDetailView(OpenAPIView):
    def get(self, request, workspace_id, knowledge_id, document_id, *args, **kwargs):
        document = DocumentService.get_document(knowledge_id, document_id)
        if document is None:
            return self.success(None, message='document not found')
        return self.success({
            'workspace_id': workspace_id,
            'knowledge_id': knowledge_id,
            'document_id': str(document.id),
            'name': document.name,
            'status': document.status,
            'status_meta': document.status_meta,
        })

    def delete(self, request, workspace_id, knowledge_id, document_id, *args, **kwargs):
        count = DocumentService.delete_document(knowledge_id, document_id)
        return self.success({
            'workspace_id': workspace_id,
            'knowledge_id': knowledge_id,
            'document_id': document_id,
            'deleted': count,
        }, message='document deleted')


class DocumentReprocessView(OpenAPIView):
    def post(self, request, workspace_id, knowledge_id, document_id, *args, **kwargs):
        document = DocumentService.get_document(knowledge_id, document_id)
        if document is None:
            return self.success(None, message='document not found')
        document = DocumentService.reprocess_document(document)
        return self.success({
            'workspace_id': workspace_id,
            'knowledge_id': knowledge_id,
            'document_id': document_id,
            'status': document.status,
            'status_meta': document.status_meta,
        }, message='document reprocess started')
