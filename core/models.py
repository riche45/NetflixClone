import uuid
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.conf import settings
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


class CustomUserManager(BaseUserManager):
    """Manager que usa el email como identificador en lugar del username."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError('El email es obligatorio')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        if extra_fields.get('is_staff') is not True:
            raise ValueError('El superusuario debe tener is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('El superusuario debe tener is_superuser=True.')
        return self._create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    email = models.EmailField(_('email address'), unique=True)
    username = models.CharField(_('username'), max_length=150, blank=True)
    first_name = models.CharField(_('first name'), max_length=30, blank=True)
    last_name = models.CharField(_('last name'), max_length=150, blank=True)
    profiles = models.ManyToManyField('Profile', blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

    def __str__(self):
        return self.email


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
        if not self.category_id:
            self.category, _created = Category.objects.get_or_create(name='Drama')

        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('core:show_det', kwargs={'movie_id': self.uuid})


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
        if not self.category_id:
            self.category, _created = Category.objects.get_or_create(name='Drama')
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
