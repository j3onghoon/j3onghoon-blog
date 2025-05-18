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


class PostListView(ListView):
    model = Post
    template_name = "post_list.html"
    htmx_template_name= "post_list_partial.html"
    paginate_by = 10



