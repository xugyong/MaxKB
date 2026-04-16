import uuid_utils.compat as uuid

from application.models import Chat, ChatRecord, ChatUserType
from chat.serializers.chat import OpenAIChatSerializer, OpenChatSerializers
from common.exception.app_exception import AppApiException
from open_api.serializers import OpenChatCompletionSerializer
from .base import OpenAPIView


class ChatCompletionView(OpenAPIView):
    def post(self, request, *args, **kwargs):
        serializer = OpenChatCompletionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated = serializer.validated_data
        application_id = validated.get('application_id')
        chat_id = validated.get('chat_id') or str(uuid.uuid7())
        messages = validated.get('messages') or []
        if len(messages) == 0:
            return self.success(None, message='messages is required')

        source = request.data.get('source') or {'origin': 'open_api'}
        open_chat_serializer = OpenChatSerializers(data={
            'application_id': application_id,
            'chat_user_id': str(uuid.uuid7()),
            'chat_user_type': ChatUserType.ANONYMOUS_USER.value,
            'ip_address': request.META.get('REMOTE_ADDR', ''),
            'source': source,
            'debug': True,
        })
        open_chat_serializer.is_valid(raise_exception=True)
        opened_chat_id = open_chat_serializer.open()
        open_ai_serializer = OpenAIChatSerializer(data={
            'application_id': application_id,
            'chat_user_id': str(uuid.uuid7()),
            'chat_user_type': ChatUserType.ANONYMOUS_USER.value,
            'ip_address': request.META.get('REMOTE_ADDR', ''),
            'source': source,
            'debug': True,
        })
        open_ai_serializer.is_valid(raise_exception=True)
        result = open_ai_serializer.chat({
            'chat_id': opened_chat_id,
            'messages': messages,
            'stream': validated.get('stream', False),
            're_chat': validated.get('re_chat', False),
            'form_data': {},
            'image_list': [],
            'document_list': [],
            'audio_list': [],
            'other_list': [],
        })

        session_id = opened_chat_id
        if isinstance(result, dict) and result.get('chat_id'):
            session_id = str(result.get('chat_id'))

        chat_record = ChatRecord.objects.filter(chat_id=session_id).order_by('-create_time').first()
        if chat_record is None:
            chat_record = ChatRecord.objects.filter(chat_id=opened_chat_id).order_by('-create_time').first()
        message_id = str(chat_record.id) if chat_record is not None else str(uuid.uuid7())
        answer_text = ''
        if chat_record is not None and getattr(chat_record, 'answer_text', None):
            answer_text = chat_record.answer_text
        elif isinstance(result, dict):
            answer_text = result.get('answer') or result.get('content') or result.get('text') or ''

        if not (answer_text or '').strip():
            raise AppApiException(502, 'chat completion failed: empty answer from upstream')

        sources = []
        def _truncate(value, limit=240):
            text = '' if value is None else str(value)
            return text if len(text) <= limit else text[:limit] + '...'

        def _push_source(src_item):
            if isinstance(src_item, dict):
                content = src_item.get('content') or src_item.get('text') or ''
                document_name = src_item.get('document_name') or src_item.get('name') or ''
                paragraph_title = src_item.get('paragraph_title') or src_item.get('title') or ''
                sources.append({
                    'document_id': str(src_item.get('document_id', '')),
                    'paragraph_id': str(src_item.get('paragraph_id', '')),
                    'document_name': document_name,
                    'paragraph_title': paragraph_title,
                    'content': _truncate(content),
                    'content_preview': _truncate(content, 96),
                    'summary': _truncate(' / '.join([part for part in [document_name, paragraph_title] if part]) or content, 128),
                    'score': src_item.get('score'),
                    'knowledge_id': str(src_item.get('knowledge_id', '')),
                })
            else:
                sources.append({'content': _truncate(src_item)})

        if chat_record is not None and isinstance(chat_record.details, dict):
            search_step = chat_record.details.get('search_step', {})
            paragraph_list = search_step.get('paragraph_list') or []
            for paragraph in paragraph_list:
                _push_source(paragraph)
        if not sources and isinstance(result, dict):
            raw_sources = result.get('sources') or []
            for src in raw_sources:
                _push_source(src)
        if not sources:
            raise AppApiException(502, 'chat completion failed: empty sources from upstream')

        if isinstance(result, dict):
            result_usage = result.get('usage') or {}
        else:
            result_usage = {}
        usage_message_tokens = result_usage.get('message_tokens')
        if usage_message_tokens is None:
            usage_message_tokens = getattr(chat_record, 'message_tokens', None) if chat_record is not None else None
        usage_answer_tokens = result_usage.get('answer_tokens')
        if usage_answer_tokens is None:
            usage_answer_tokens = getattr(chat_record, 'answer_tokens', None) if chat_record is not None else None
        usage_total_tokens = result_usage.get('total_tokens')
        if usage_total_tokens is None and usage_message_tokens is not None and usage_answer_tokens is not None:
            usage_total_tokens = usage_message_tokens + usage_answer_tokens
        usage_extra = result_usage.get('extra') if isinstance(result_usage, dict) else None
        if usage_extra is None:
            usage_extra = {
                'model_name': result_usage.get('model_name') if isinstance(result_usage, dict) else None,
                'prompt_tokens': result_usage.get('prompt_tokens') if isinstance(result_usage, dict) else None,
                'completion_tokens': result_usage.get('completion_tokens') if isinstance(result_usage, dict) else None,
            }
        if usage_message_tokens is None or usage_answer_tokens is None or usage_total_tokens is None:
            raise AppApiException(502, 'chat completion failed: invalid usage statistics from upstream')
        if usage_total_tokens <= 0:
            raise AppApiException(502, 'chat completion failed: usage total_tokens must be greater than 0')
        status = 'ok' if chat_record is not None or answer_text else 'pending'
        finish_reason = (result.get('finish_reason') if isinstance(result, dict) else None) or 'stop'

        return self.success({
            'session_id': session_id,
            'message_id': message_id,
            'answer': answer_text,
            'sources': sources,
            'usage': {
                'message_tokens': usage_message_tokens,
                'answer_tokens': usage_answer_tokens,
                'total_tokens': usage_total_tokens,
                'extra': usage_extra,
            },
            'finish_reason': finish_reason,
            'stream': validated.get('stream', False),
            'status': status,
        }, message='chat completion ok')


class ChatSessionListView(OpenAPIView):
    def get(self, request, *args, **kwargs):
        application_id = request.query_params.get('application_id')
        chat_user_id = request.query_params.get('chat_user_id')
        queryset = Chat.objects.filter(is_deleted=False).order_by('-update_time')
        if application_id:
            queryset = queryset.filter(application_id=application_id)
        if chat_user_id:
            queryset = queryset.filter(chat_user_id=chat_user_id)
        data = [{
            'id': str(item.id),
            'application_id': str(item.application_id),
            'chat_user_id': item.chat_user_id,
            'chat_user_type': item.chat_user_type,
            'abstract': item.abstract,
            'chat_record_count': item.chat_record_count,
            'star_num': item.star_num,
            'trample_num': item.trample_num,
            'last_message_preview': item.abstract[:120] if item.abstract else '',
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
        serializer = OpenChatSerializers(data={
            'application_id': request.data.get('application_id'),
            'chat_user_id': request.data.get('chat_user_id') or str(uuid.uuid7()),
            'chat_user_type': request.data.get('chat_user_type') or ChatUserType.ANONYMOUS_USER.value,
            'ip_address': request.META.get('REMOTE_ADDR', ''),
            'source': request.data.get('source') or {'origin': 'open_api'},
            'debug': True,
        })
        serializer.is_valid(raise_exception=True)
        session_id = serializer.open()
        chat = Chat.objects.filter(id=session_id).first()
        return self.created({
            'session_id': session_id,
            'application_id': str(chat.application_id) if chat is not None else '',
            'chat_user_id': chat.chat_user_id if chat is not None else '',
            'chat_user_type': chat.chat_user_type if chat is not None else '',
            'abstract': chat.abstract if chat is not None else '',
            'chat_record_count': chat.chat_record_count if chat is not None else 0,
            'star_num': chat.star_num if chat is not None else 0,
            'trample_num': chat.trample_num if chat is not None else 0,
            'last_message_preview': chat.abstract[:120] if chat is not None and chat.abstract else '',
            'create_time': chat.create_time if chat is not None else None,
            'update_time': chat.update_time if chat is not None else None,
        }, message='chat session created')


class ChatSessionDetailView(OpenAPIView):
    def get(self, request, session_id, *args, **kwargs):
        chat = Chat.objects.filter(id=session_id).first()
        if chat is None:
            return self.success(None, message='chat not found')
        return self.success({
            'session_id': session_id,
            'application_id': str(chat.application_id),
            'chat_user_id': chat.chat_user_id,
            'chat_user_type': chat.chat_user_type,
            'abstract': chat.abstract,
            'chat_record_count': chat.chat_record_count,
            'star_num': chat.star_num,
            'trample_num': chat.trample_num,
            'last_message_preview': chat.abstract[:120] if chat.abstract else '',
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
            'index': item.index,
            'problem_text': item.problem_text,
            'answer_text': item.answer_text,
            'message_tokens': item.message_tokens,
            'answer_tokens': item.answer_tokens,
            'vote_status': item.vote_status,
            'vote_reason': item.vote_reason,
            'details': item.details,
            'create_time': item.create_time,
            'update_time': item.update_time,
        } for item in items]
        return self.success({
            'session_id': session_id,
            'items': data,
            'page': 1,
            'page_size': len(data),
            'total': len(data),
        })
