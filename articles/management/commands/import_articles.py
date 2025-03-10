import csv
from django.core.management.base import BaseCommand
from articles.models import Article, Author, Topic
from django.db import transaction
from textblob import TextBlob
import re

class Command(BaseCommand):
    help = 'Import articles from a CSV file into normalized database tables'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path to the CSV file')

    def extract_topics(self, text, title):
        # Combine title and text for better topic extraction
        full_text = f"{title}. {text}"
        
        # Extract noun phrases using TextBlob
        blob = TextBlob(full_text)
        noun_phrases = blob.noun_phrases
        
        # Filter and clean topics
        topics = set()
        for phrase in noun_phrases:
            # Clean the phrase
            clean_phrase = re.sub(r'[^\w\s]', '', phrase).strip().lower()
            if len(clean_phrase.split()) <= 3 and len(clean_phrase) > 3:  # Avoid too long or too short phrases
                topics.add(clean_phrase)
        
        return list(topics)[:5]  # Return top 5 topics

    @transaction.atomic
    def handle(self, *args, **kwargs):
        csv_file = kwargs['csv_file']

        with open(csv_file, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                # Get or create author
                author, _ = Author.objects.get_or_create(
                    name=row['author']
                )
                
                # Create article
                article = Article.objects.create(
                    title=row['title'],
                    author=author,
                    _claps_str=row['claps'],
                    reading_time=int(float(row['reading_time'])),
                    link=row['link'],
                    text=row['text']
                )
                
                # Extract and create topics
                topics = self.extract_topics(row['text'], row['title'])
                for topic_name in topics:
                    topic, created = Topic.objects.get_or_create(name=topic_name)
                    topic.articles.add(article)
                    if created:
                        topic.article_count = 1
                    else:
                        topic.article_count = topic.articles.count()
                    topic.save()
                
                # Update author statistics
                author.article_count = author.articles.count()
                author.total_claps = sum(article.claps for article in author.articles.all())
                author.save()

        self.stdout.write(self.style.SUCCESS(f'Successfully imported articles from {csv_file}'))
