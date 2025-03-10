from django.core.management.base import BaseCommand
from django.db.models import Count
from articles.models import Article, Author
from django.db import transaction

class Command(BaseCommand):
    help = 'Remove duplicate articles based on title and author'

    def handle(self, *args, **kwargs):
        self.stdout.write('Starting duplicate removal process...')
        
        # Find duplicates based on title and author
        duplicates = (
            Article.objects.values('title', 'author')
            .annotate(count=Count('id'))
            .filter(count__gt=1)
        )
        
        total_duplicates = 0
        
        with transaction.atomic():
            # Process each set of duplicates
            for dup in duplicates:
                # Get all articles with this title and author
                articles = Article.objects.filter(
                    title=dup['title'],
                    author_id=dup['author']
                ).order_by('id')  # Keep the first one created
                
                # Keep the first article, delete the rest
                first_article = articles.first()
                to_delete = articles.exclude(id=first_article.id)
                
                count = to_delete.count()
                total_duplicates += count
                
                # Delete duplicates
                to_delete.delete()
                
                self.stdout.write(f'Deleted {count} duplicates of article "{dup["title"]}"')
            
            # Update author statistics
            for author in Author.objects.all():
                author.update_stats()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully removed {total_duplicates} duplicate articles'
            )
        ) 