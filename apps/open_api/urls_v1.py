from django.urls import path

from .views.auth import TokenView, MeView, ApiKeyListView, ApiKeyDetailView
from .views.knowledge import KnowledgeListView, KnowledgeDetailView
from .views.document import DocumentListView, DocumentDetailView, DocumentReprocessView
from .views.chat import ChatCompletionView, ChatSessionListView, ChatSessionDetailView, ChatSessionMessageListView

urlpatterns = [
    path('auth/token', TokenView.as_view()),
    path('auth/me', MeView.as_view()),
    path('workspaces/<str:workspace_id>/applications/<str:application_id>/api-keys', ApiKeyListView.as_view()),
    path('workspaces/<str:workspace_id>/applications/<str:application_id>/api-keys/<str:api_key_id>', ApiKeyDetailView.as_view()),
    path('workspaces/<str:workspace_id>/knowledgebases', KnowledgeListView.as_view()),
    path('workspaces/<str:workspace_id>/knowledgebases/<str:knowledge_id>', KnowledgeDetailView.as_view()),
    path('workspaces/<str:workspace_id>/knowledgebases/<str:knowledge_id>/documents', DocumentListView.as_view()),
    path('workspaces/<str:workspace_id>/knowledgebases/<str:knowledge_id>/documents/<str:document_id>', DocumentDetailView.as_view()),
    path('workspaces/<str:workspace_id>/knowledgebases/<str:knowledge_id>/documents/<str:document_id>/reprocess', DocumentReprocessView.as_view()),
    path('chat/completions', ChatCompletionView.as_view()),
    path('chat/sessions', ChatSessionListView.as_view()),
    path('chat/sessions/<str:session_id>', ChatSessionDetailView.as_view()),
    path('chat/sessions/<str:session_id>/messages', ChatSessionMessageListView.as_view()),
]
