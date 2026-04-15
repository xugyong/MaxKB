from typing import Optional

from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string

from application.models import ApplicationApiKey, Application
from knowledge.models import Knowledge, Document, State


class KnowledgeService:
    @staticmethod
    def list_knowledge(workspace_id: str):
        return Knowledge.objects.filter(workspace_id=workspace_id).order_by('-create_time')

    @staticmethod
    def create_knowledge(workspace_id: str, user=None, **kwargs) -> Knowledge:
        folder_id = kwargs.get('folder_id') or workspace_id
        UserModel = get_user_model()
        if user is not None and not isinstance(user, UserModel):
            user = None
        return Knowledge.objects.create(
            workspace_id=workspace_id,
            user=user,
            name=kwargs.get('name', ''),
            desc=kwargs.get('desc', '') or '',
            folder_id=folder_id,
            embedding_model_id=kwargs.get('embedding_model_id'),
        )

    @staticmethod
    def get_knowledge(workspace_id: str, knowledge_id: str) -> Optional[Knowledge]:
        return Knowledge.objects.filter(workspace_id=workspace_id, id=knowledge_id).first()


class DocumentService:
    @staticmethod
    def list_documents(knowledge: Knowledge):
        return Document.objects.filter(knowledge=knowledge).order_by('-create_time')

    @staticmethod
    def get_document(knowledge_id: str, document_id: str) -> Optional[Document]:
        return Document.objects.filter(knowledge_id=knowledge_id, id=document_id).first()

    @staticmethod
    def delete_document(knowledge_id: str, document_id: str) -> int:
        deleted, _ = Document.objects.filter(knowledge_id=knowledge_id, id=document_id).delete()
        return deleted

    @staticmethod
    def _sync_status(document: Document):
        document.status = State.STARTED.value + State.PENDING.value + State.PENDING.value
        document.save(update_fields=['status'])

    @staticmethod
    def create_from_text(workspace_id: str, knowledge: Knowledge, name: str, text: str, user=None):
        document = Document.objects.create(
            knowledge=knowledge,
            name=name or 'document',
            char_length=len(text or ''),
            type=knowledge.type,
            meta={'source': 'open_api', 'workspace_id': workspace_id, 'text_preview': (text or '')[:200]},
            status=State.STARTED.value + State.PENDING.value + State.PENDING.value,
        )
        return document.id

    @staticmethod
    def create_from_file(workspace_id: str, knowledge: Knowledge, uploaded_file, name: str = None):
        file_name = getattr(uploaded_file, 'name', '') or name or 'document'
        suffix = (file_name.rsplit('.', 1)[-1] if '.' in file_name else '').lower()
        if suffix in {'txt', 'md', 'markdown', 'log', 'csv'}:
            content = uploaded_file.read()
            try:
                text = content.decode('utf-8')
            except Exception:
                text = content.decode('utf-8', errors='ignore')
            return DocumentService.create_from_text(workspace_id, knowledge, file_name, text)
        content = uploaded_file.read()
        try:
            text = content.decode('utf-8')
        except Exception:
            text = content.decode('utf-8', errors='ignore')
        if not text.strip():
            text = f'uploaded file: {file_name}'
        return DocumentService.create_from_text(workspace_id, knowledge, file_name, text)

    @staticmethod
    def reprocess_document(document: Document):
        document.status = State.STARTED.value + State.PENDING.value + State.PENDING.value
        document.save(update_fields=['status'])
        return document


class ApiKeyService:
    @staticmethod
    def list_api_keys(application_id: str):
        return ApplicationApiKey.objects.filter(application_id=application_id).order_by('-create_time')

    @staticmethod
    def create_api_key(application_id: str, workspace_id: str, **kwargs) -> ApplicationApiKey:
        application = Application.objects.filter(id=application_id, workspace_id=workspace_id).first()
        if application is None:
            raise ValueError('application not found')
        token = get_random_string(64)
        return ApplicationApiKey.objects.create(
            application=application,
            workspace_id=workspace_id,
            secret_key=token,
            allow_cross_domain=kwargs.get('allow_cross_domain', False),
            cross_domain_list=kwargs.get('cross_domain_list', []),
            expire_time=kwargs.get('expire_time'),
            is_permanent=kwargs.get('is_permanent', True),
        )

    @staticmethod
    def update_api_key(api_key: ApplicationApiKey, **kwargs) -> ApplicationApiKey:
        for field in ['is_active', 'allow_cross_domain', 'cross_domain_list', 'expire_time', 'is_permanent']:
            if field in kwargs and kwargs[field] is not None:
                setattr(api_key, field, kwargs[field])
        api_key.save()
        return api_key

    @staticmethod
    def delete_api_key(api_key: ApplicationApiKey) -> int:
        deleted, _ = ApplicationApiKey.objects.filter(id=api_key.id).delete()
        return deleted
