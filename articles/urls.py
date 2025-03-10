from django.urls import path
from .views import (
    ArticleListView, 
    ArticleDetailView, 
    AuthorDetailView,
    ArticleCreateView,
    ArticleDeleteView,
)

urlpatterns = [
    path('', ArticleListView.as_view(), name='article-list'),
    path('article/add/', ArticleCreateView.as_view(), name='article-create'),
    path('article/<int:pk>/', ArticleDetailView.as_view(), name='article-detail'),
    path('article/<int:pk>/delete/', ArticleDeleteView.as_view(), name='article-delete'),
    path('author/<int:pk>/', AuthorDetailView.as_view(), name='author-detail'),
] 