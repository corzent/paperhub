from django.db import models
from django.db.models import Count

def convert_claps_to_number(claps_str):
    """Convert clap string (e.g., '3.2k', '45') to actual number."""
    try:
        if not claps_str:
            return 0
        
        claps_str = claps_str.lower().strip()
        if 'k' in claps_str:
            number = float(claps_str.replace('k', ''))
            return int(number * 1000)
        return int(float(claps_str))
    except (ValueError, TypeError):
        return 0

class Author(models.Model):
    name = models.CharField(max_length=1000, unique=True)
    article_count = models.PositiveIntegerField(default=0)
    total_claps = models.PositiveIntegerField(default=0)

    def update_stats(self):
        """Update author statistics."""
        self.article_count = self.articles.count()
        self.total_claps = sum(article.claps for article in self.articles.all())
        self.save()

    def get_top_topics(self, limit=5):
        """Get author's most written-about topics."""
        return Topic.objects.filter(
            articles__author=self
        ).annotate(
            topic_count=Count('articles')
        ).order_by('-topic_count')[:limit]

    def get_popular_articles(self, limit=5):
        """Get author's most popular articles by claps."""
        return self.articles.all().order_by('-claps')[:limit]

    def __str__(self) -> str:
        return str(self.name)

    class Meta:
        ordering = ['-article_count']

class Article(models.Model):
    title = models.CharField(max_length=1000)
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name='articles')
    _claps_str = models.CharField(max_length=100, db_column='claps')  # Use existing 'claps' column
    reading_time = models.IntegerField()
    link = models.URLField(max_length=2000)
    text = models.TextField()

    @property
    def claps(self):
        """Get numeric value of claps."""
        return convert_claps_to_number(self._claps_str)

    @claps.setter
    def claps(self, value):
        """Set claps value, storing as string."""
        self._claps_str = str(value)

    def __str__(self) -> str:
        return str(self.title)

    class Meta:
        ordering = ['-reading_time']  # Changed to reading_time since we removed created_at

class Topic(models.Model):
    name = models.CharField(max_length=100, unique=True)
    articles = models.ManyToManyField(Article, related_name='topics')
    article_count = models.PositiveIntegerField(default=0)

    def __str__(self) -> str:
        return str(self.name)

    class Meta:
        ordering = ['-article_count']
