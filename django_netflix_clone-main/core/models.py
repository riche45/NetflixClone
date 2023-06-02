import uuid
from django.conf import settings
from django.contrib.auth.models import AbstractUser, User
from django.db import models
from django.core.management import call_command
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.urls import reverse
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from autoslug import AutoSlugField


AGE_CHOICES = (
    ('All', 'All'),
    ('Kids', 'Kids')
)

MOVIE_TYPE = (
    ('single', 'Single'),
    ('seasonal', 'Seasonal')
)


class CustomUser(AbstractUser):
    profiles = models.ManyToManyField('Profile')


class Profile(models.Model):
    name = models.CharField(max_length=225)
    age_limit = models.CharField(max_length=5, choices=AGE_CHOICES)
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)

    def __str__(self):
        return self.name + " "+self.age_limit


class Category(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['name']
        verbose_name = _('category')
        verbose_name_plural = _('categories')

    def __str__(self):
        return self.name


class Movie(models.Model):
    MOVIE_TYPE = (
        ('movie', 'Movie'),
        ('series', 'Series'),
    )

    AGE_CHOICES = (
        ('G', 'G - General Audiences'),
        ('PG', 'PG - Parental Guidance Suggested'),
        ('PG-13', 'PG-13 - Parents Strongly Cautioned'),
        ('R', 'R - Restricted'),
        ('NC-17', 'NC-17 - Adults Only'),
    )
    title = models.CharField(max_length=225)
    slug = AutoSlugField(unique=True, populate_from='title', default='default-slug')
    description = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    type = models.CharField(max_length=15, choices=MOVIE_TYPE)
    videos = models.ManyToManyField('Video')
    flyer = models.ImageField(upload_to='flyers', blank=True, null=True)
    age_limit = models.CharField(max_length=5, choices=AGE_CHOICES, blank=True, null=True)
    duration = models.PositiveIntegerField(default=120)
    cover_image = models.ImageField(upload_to='movie_covers')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.category:
            self.category = Category.objects.get(name='Drama')

        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('movie_detail', kwargs={'uuid': self.uuid})


class Series(models.Model):
    title = models.CharField(max_length=200)
    num_seasons = models.PositiveIntegerField(default=3)
    num_episodes = models.PositiveIntegerField(default=8)
    episode_duration = models.PositiveIntegerField(default=60)
    description = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    type = models.CharField(max_length=10, choices=MOVIE_TYPE)
    videos = models.ManyToManyField('Video')
    flyer = models.ImageField(upload_to='flyers', blank=True, null=True)
    age_limit = models.CharField(max_length=5, choices=AGE_CHOICES, blank=True, null=True)
    cover_image = models.ImageField(upload_to='movie_covers')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.category:
            self.category = Category.objects.get(name='Drama')
        super().save(*args, **kwargs)


class Video(models.Model):
    title = models.CharField(max_length=225, blank=True, null=True)
    file = models.FileField(upload_to='movies')


class Season(models.Model):
    title = models.CharField(max_length=200)
    plot = models.TextField()
    number = models.PositiveIntegerField(unique=True)
    release_date = models.DateField()
    series = models.ForeignKey(Series, on_delete=models.CASCADE, related_name='seasons')

    def __str__(self):
        return self.title


class Episode(models.Model):
    title = models.CharField(max_length=200)
    plot = models.TextField()
    number = models.PositiveIntegerField(unique=True)
    release_date = models.DateField()
    season = models.ForeignKey(Season, on_delete=models.CASCADE, related_name='episodes')

    def __str__(self):
        return self.title


class Watched(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, null=True, blank=True)
    series = models.ForeignKey(Series, on_delete=models.CASCADE, null=True, blank=True)
    season = models.ForeignKey(Season, on_delete=models.CASCADE, null=True, blank=True)
    episode = models.ForeignKey(Episode, on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        unique_together = ('user', 'movie', 'series', 'season', 'episode')


class Favorite(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, null=True, blank=True)
    series = models.ForeignKey(Series, on_delete=models.CASCADE, null=True, blank=True)
    season = models.ForeignKey(Season, on_delete=models.CASCADE, null=True, blank=True)
    episode = models.ForeignKey(Episode, on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        unique_together = ('user', 'movie', 'series', 'season', 'episode')


category, created = Category.objects.get_or_create(
    name='Drama',
    defaults={'description': 'This is a description for the Drama category'})

if not created:
    category.description = 'fiction and often by a tragic ending.'
    category.save()

movie = Movie.objects.create(
    title='My Movie',
    description='A description',
    type='single',
    flyer='flyer.jpg',
    age_limit='G',
    duration=120,
    cover_image='cover.jpg',
    category=category
)

category, created = Category.objects.get_or_create(
    name='Drama',
    defaults={'description': 'This is a description for the Drama category'})

if not created:
    category.description = 'fiction and often by a tragic ending.'
    category.save()

series = Series.objects.create(
    title='My Series',
    num_seasons=5,
    num_episodes=10,
    episode_duration=45,
    description='A description',
    type='Serie',
    flyer='flyer.jpg',
    age_limit='PG',
    cover_image='cover.jpg',
    category=category
)


@receiver(post_migrate)
def add_category(sender, **kwargs):
    from core.models import Category
    category_slug = "Drama"
    existing_categories = Category.objects.filter(slug=category_slug)
    if existing_categories.exists():
        print(f"Category '{existing_categories[0].name}' already exists.")
    else:
        new_category = Category.objects.create(slug=category_slug, name="Drama")
        print(f"Category '{new_category.name}' created.")
