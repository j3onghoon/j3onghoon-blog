from django.views.generic import ListView, DetailView, TemplateView
from django.db.models import Count

from .models import User, Post, Comment, Attachment, Category


class HomeView(TemplateView):
    template_name = "home.html"


class PostBaseListView(ListView):
    model = Post
    paginate_by = 10

    # todo 캐시 추가
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        return self.model.objects.filter(type=self.post_type)\
            .annotate(comments_count=Count("comments"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_range"] = self.get_paginator(self.get_queryset(), 10).get_elided_page_range()
        print("hello", context)
        return context

    def get_template_names(self):
        if "HX-Request" in self.request.headers:
            return [f"{self.post_type}_list_partial.html"]
        return [f"{self.post_type}_list.html"]

    def get_context_object_name(self, object_list):
        return f"{self.post_type}s"


class PostListView(PostBaseListView):
    post_type = "post"


class PostDetailView(DetailView):
    model = Post

    def get_queryset(self):
        return self.model.objects.prefetch_related("comments", "comments__author")


class GuestBookListView(PostBaseListView):
    post_type = "guestbook"


class PortfolioListView(PostBaseListView):
    post_type = "portfolio"
