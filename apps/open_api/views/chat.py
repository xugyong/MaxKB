from application.models import Chat, ChatRecord
from common.auth.authenticate import ChatTokenAuth
from open_api.serializers import OpenChatCompletionSerializer
from open_api.services import KnowledgeService
from .base import OpenAPIView


class ChatCompletionView(OpenAPIView):
    def post(self, request, *args, **kwargs):
        serializer = OpenChatCompletionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return self.success({
            'session_id': serializer.validated_data.get('chat_id') or '',
            'message_id': '',
            'answer': '',
            'sources': [],
            'stream': serializer.validated_data.get('stream', False),
            'status': 'stub',
        }, message='chat completion endpoint stub')


class ChatSessionListView(OpenAPIView):
    def get(self, request, *args, **kwargs):
        application_id = request.query_params.get('application_id')
        if application_id:
            queryset = Chat.objects.filter(application_id=application_id, is_deleted=False).order_by('-update_time')
        else:
            queryset = Chat.objects.none()
        data = [{
            'id': str(item.id),
            'application_id': str(item.application_id),
            'abstract': item.abstract,
            'create_time': item.create_time,
            'update_time': item.update_time,
        } for item in queryset]
        return self.success({
            'items': data,
            'page': 1,
            'page_size': len(data),
            'total': len(data),
        })

    def post(self, request, *args, **kwargs):
        return self.created({
            'session_id': '',
        }, message='chat session create endpoint stub')


class ChatSessionDetailView(OpenAPIView):
    def get(self, request, session_id, *args, **kwargs):
        chat = Chat.objects.filter(id=session_id).first()
        if chat is None:
            return self.success(None, message='chat not found')
        return self.success({
            'session_id': session_id,
            'application_id': str(chat.application_id),
            'abstract': chat.abstract,
            'create_time': chat.create_time,
            'update_time': chat.update_time,
        })

    def delete(self, request, session_id, *args, **kwargs):
        deleted = Chat.objects.filter(id=session_id).update(is_deleted=True)
        return self.success({
            'session_id': session_id,
            'deleted': deleted,
        }, message='chat session deleted')


class ChatSessionMessageListView(OpenAPIView):
    def get(self, request, session_id, *args, **kwargs):
        items = ChatRecord.objects.filter(chat_id=session_id).order_by('create_time')
        data = [{
            'id': str(item.id),
            'chat_id': str(item.chat_id),
            'problem_text': item.problem_text,
            'answer_text': item.answer_text,
            'vote_status': item.vote_status,
            'create_time': item.create_time,
            'update_time': item.update_time,
        } for item in items]
        return self.success({
            'session_id': session_id,
            'items': data,
            'total': len(data),
        })
