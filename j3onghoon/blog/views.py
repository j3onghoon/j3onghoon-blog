from django.views.generic import ListView, DetailView, TemplateView
from django.db.models import Count

from .models import User, Post, Comment, Attachment, Category


class HomeView(TemplateView):
    template_name = "home.html"


class PostBaseListView(ListView):
    model = Post
    paginate_by = 8

    # todo 캐시 추가
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        return self.model.objects.filter(type=self.post_type)\
            .annotate(comments_count=Count("comments"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["elided_page_range"] = context["paginator"].get_elided_page_range(
            number=context["page_obj"].number,
            on_each_side=2,
            on_ends=1,
        )
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
    template_name = "post_detail.html"

    def get_queryset(self):
        return self.model.objects.prefetch_related("comments", "comments__author")


class GuestBookListView(PostBaseListView):
    post_type = "guestbook"


class PortfolioListView(PostBaseListView):
    post_type = "portfolio"
