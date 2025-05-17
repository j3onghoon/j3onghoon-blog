from django.views.generic import ListView, DetailView, TemplateView

from .models import User, Post, Comment, Attachment, Category


class HomeView(TemplateView):
    template_name = "home.html"

class PostListView(ListView):
    model = Post
    paginate_by = 10


class PostDetailView(DetailView):
    model = Post