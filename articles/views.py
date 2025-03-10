from django.shortcuts import render
from django.views.generic import ListView, DetailView, CreateView, DeleteView
from django.db.models import Q
from django.urls import reverse_lazy
from .models import Article, Author, Topic

# Create your views here.

class ArticleListView(ListView):
    model = Article
    template_name = 'articles/article_list.html'
    context_object_name = 'articles'
    paginate_by = 6

    def get_ordering(self):
        # Get the sort parameter from URL, default to '-reading_time'
        sort_by = self.request.GET.get('sort', '-reading_time')
        # Define allowed sorting fields
        allowed_sorts = {
            'reading_time': 'reading_time',
            '-reading_time': '-reading_time',
            'claps': '_claps_str',
            '-claps': '-_claps_str',
            'author': 'author__name',
            '-author': '-author__name',
            'title': 'title',
            '-title': '-title',
        }
        return allowed_sorts.get(sort_by, '-reading_time')

    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(author__name__icontains=search_query)
            )
        return queryset.order_by(self.get_ordering())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        context['current_sort'] = self.request.GET.get('sort', '-reading_time')
        # Add top authors and topics
        context['top_authors'] = Author.objects.order_by('-total_claps')[:5]
        context['popular_topics'] = Topic.objects.order_by('-article_count')[:10]
        return context

class ArticleDetailView(DetailView):
    model = Article
    template_name = 'articles/article_detail.html'
    context_object_name = 'article'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        article = self.get_object()
        context['related_articles'] = Article.objects.filter(
            topics__in=article.topics.all()
        ).exclude(
            id=article.id
        ).distinct()[:3]
        return context

class ArticleCreateView(CreateView):
    model = Article
    template_name = 'articles/article_form.html'
    fields = ['title', 'author', 'text', 'reading_time', 'link']
    success_url = reverse_lazy('article-list')

    def form_valid(self, form):
        response = super().form_valid(form)
        # Extract and create topics
        from .management.commands.import_articles import Command
        topics = Command().extract_topics(form.cleaned_data['text'], form.cleaned_data['title'])
        for topic_name in topics:
            topic, created = Topic.objects.get_or_create(name=topic_name)
            topic.articles.add(self.object)
            if created:
                topic.article_count = 1
            else:
                topic.article_count = topic.articles.count()
            topic.save()
        
        # Update author statistics
        self.object.author.update_stats()
        return response

class ArticleDeleteView(DeleteView):
    model = Article
    success_url = reverse_lazy('article-list')
    
    def delete(self, request, *args, **kwargs):
        article = self.get_object()
        author = article.author
        response = super().delete(request, *args, **kwargs)
        # Update author statistics after deletion
        author.update_stats()
        return response

class AuthorDetailView(DetailView):
    model = Author
    template_name = 'articles/author_detail.html'
    context_object_name = 'author'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        author = self.get_object()
        
        # Get all articles by the author, sorted by claps
        context['popular_articles'] = author.articles.all().order_by('-_claps_str')
        context['top_topics'] = author.get_top_topics()
        context['stats'] = {
            'total_claps': author.total_claps,
            'article_count': author.article_count,
        }
        return context
