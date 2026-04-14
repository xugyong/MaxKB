from rest_framework import serializers


class PaginationSerializer(serializers.Serializer):
    current_page = serializers.IntegerField(required=False, default=1, min_value=1)
    page_size = serializers.IntegerField(required=False, default=20, min_value=1, max_value=200)


class KnowledgeCreateSerializer(serializers.Serializer):
    name = serializers.CharField(required=True, max_length=150)
    desc = serializers.CharField(required=False, allow_blank=True, allow_null=True, default='')
    folder_id = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    embedding_model_id = serializers.CharField(required=False, allow_blank=True, allow_null=True)


class KnowledgeUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(required=False, max_length=150)
    desc = serializers.CharField(required=False, allow_blank=True, allow_null=True)


class DocumentUploadSerializer(serializers.Serializer):
    name = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=150)
    file = serializers.FileField(required=False)
    text = serializers.CharField(required=False, allow_blank=True, allow_null=True)


class OpenChatMessageSerializer(serializers.Serializer):
    role = serializers.CharField(required=True)
    content = serializers.CharField(required=True)


class OpenChatCompletionSerializer(serializers.Serializer):
    application_id = serializers.CharField(required=True)
    chat_id = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    stream = serializers.BooleanField(required=False, default=False)
    re_chat = serializers.BooleanField(required=False, default=False)
    messages = serializers.ListField(child=OpenChatMessageSerializer(), required=True)


class ApiKeyCreateSerializer(serializers.Serializer):
    application_id = serializers.CharField(required=True)
    allow_cross_domain = serializers.BooleanField(required=False, default=False)
    cross_domain_list = serializers.ListField(child=serializers.CharField(), required=False, default=list)
    expire_time = serializers.DateTimeField(required=False, allow_null=True)
    is_permanent = serializers.BooleanField(required=False, default=True)


class ApiKeyUpdateSerializer(serializers.Serializer):
    is_active = serializers.BooleanField(required=False)
    allow_cross_domain = serializers.BooleanField(required=False)
    cross_domain_list = serializers.ListField(child=serializers.CharField(), required=False)
    expire_time = serializers.DateTimeField(required=False, allow_null=True)
    is_permanent = serializers.BooleanField(required=False)
