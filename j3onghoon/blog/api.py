from rest_framework import viewsets, serializers
from rest_framework.pagination import PageNumberPagination

from .models import User, Post, Comment, Attachment, Category


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.prefetch_related("attachments")
    serializer_class = UserSerializer


class PostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post


class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.prefetch_related("attachments").select_related("author", "category")
    serializer_class = PostSerializer


class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment


class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.select_related("post", "author", "parent")
    serializer_class = CommentSerializer
