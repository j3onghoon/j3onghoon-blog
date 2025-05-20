from django.views.generic import ListView, DetailView, TemplateView

from .models import User, Post, Comment, Attachment, Category


class HomeView(TemplateView):
    template_name = "home.html"


class HTMXMixin:
    def get_template_names(self):
        if self.request.headers.get("HX-Request"):
            htmx_template = getattr(self, "htmx_template_name", None)
            if htmx_template:
                return [htmx_template]
        return super().get_template_names()


class PostBaseListView(ListView):
    model = Post
    paginate_by = 10

    def get_queryset(self):
        return self.model.objects.filter(type=self.post_type)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

    def get_template_names(self):
        if "HX-Request" in self.request.headers:
            return [f"{self.post_type}_list_partial.html"]
        return [f"{self.post_type}_list.html"]

    def get_context_object_name(self, object_list):
        return f"{self.post_type}s"


class PostListView(PostBaseListView):
    post_type = "post"


class GuestBookListView(PostBaseListView):
    post_type = "guestbook"


class PortfolioListView(PostBaseListView):
    post_type = "portfolio"
