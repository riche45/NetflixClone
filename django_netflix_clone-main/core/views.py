import plotly.graph_objs as go
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.shortcuts import redirect, render, get_object_or_404
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import DetailView
from django.views.generic.list import ListView
from matplotlib.pyplot import plot
from plotly.subplots import make_subplots

from .analytics import calculate_total_duration
from .forms import ProfileForm, CategoryForm, MovieForm, SeriesForm
from .models import Movie, Profile, Category, Series, Watched, Favorite, Season, Episode


class Home(View):
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(to='/profile/')
        category = Category.objects.filter(name='Drama').first()
        return render(request, 'index.html', {'category': category})


def index(request):
    return render(request, 'index.html')


@method_decorator(login_required, name='dispatch')
class ProfileList(View):
    def get(self, request, *args, **kwargs):
        profiles = request.user.profiles.all()
        return render(request, 'profile_list.html', {
            'profiles': profiles
        })


@method_decorator(login_required, name='dispatch')
class ProfileCreate(View):
    def get(self, request, *args, **kwargs):
        form = ProfileForm()
        return render(request, 'profileCreate.html', {
            'form': form
        })

    def post(self, request, *args, **kwargs):
        form = ProfileForm(request.POST or None)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            profile.save()
            return redirect(f'/watch/{profile.uuid}')
        return render(request, 'profileCreate.html', {
            'form': form
        })


@method_decorator(login_required, name='dispatch')
class Watch(View):
    def get(self, request, profile_id, *args, **kwargs):
        try:
            profile = Profile.objects.get(uuid=profile_id)
            movies = Movie.objects.filter(age_limit=profile.age_limit)
            showcase = movies.first() if movies.exists() else None
            if profile not in request.user.profiles.all():
                return redirect(to='core:profile_list')
            return render(request, 'movieList.html', {
                'movies': movies,
                'showcase': showcase
            })
        except Profile.DoesNotExist:
            return redirect(to='core:profile_list')


@method_decorator(login_required, name='dispatch')
class ShowMovieDetail(View):
    def get(self, request, movie_id, *args, **kwargs):
        try:
            movie = Movie.objects.get(uuid=movie_id)
            return render(request, 'movieDetail.html', {
                'movie': movie
            })
        except Movie.DoesNotExist:
            return redirect('core:profile_list')


@method_decorator(login_required, name='dispatch')
class ShowMovie(View):
    def get(self, request, movie_id, *args, **kwargs):
        try:
            movie = Movie.objects.get(uuid=movie_id)
            movie = movie.videos.values()
            return render(request, 'showMovie.html', {
                'movie': list(movie)
            })
        except Movie.DoesNotExist:
            return redirect(to='core:profile_list')


@method_decorator(login_required, name='dispatch')
class CategoryCreate(View):
    def get(self, request, *args, **kwargs):
        form = CategoryForm()
        return render(request, 'categoryCreate.html', {
            'form': form
        })

    def post(self, request, *args, **kwargs):
        form = CategoryForm(request.POST or None)
        if form.is_valid():
            category = form.save()
            return redirect(to='core:category_list')
        else:
            return render(request, 'categoryCreate.html', {
                'form': form
            })


class MovieCreate(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        form = MovieForm()
        return render(request, 'movieCreate.html', {'form': form})

    def post(self, request, *args, **kwargs):
        form = MovieForm(request.POST, request.FILES)
        if form.is_valid():
            movie = form.save(commit=False)
            category_id = form.cleaned_data.get('category')
            if category_id:
                category = Category.objects.get(id=category_id)
                movie.category = category
            movie.save()
            return redirect(f'/movie/{movie.uuid}')
        return render(request, 'movieCreate.html', {'form': form})


class SeriesCreate(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        form = SeriesForm()
        return render(request, 'seriesCreate.html', {'form': form})

    def post(self, request, *args, **kwargs):
        form = SeriesForm(request.POST, request.FILES)
        if form.is_valid():
            series = form.save(commit=False)
            category_id = form.cleaned_data.get('category_id')
            if category_id:
                categories = Category.objects.filter(id=category_id)
                if categories.exists():
                    series.category = categories.first()
                else:
                    series.category = Category.objects.get(name='Drama')
            else:
                series.category = Category.objects.get(name='Drama')
            series.save()
            return redirect(f'/series/{series.uuid}')
        return render(request, 'seriesCreate.html', {'form': form})


class MovieListView(ListView):
    model = Movie
    template_name = 'movieList.html'
    context_object_name = 'movies'
    paginate_by = 10


class SeriesListView(ListView):
    model = Series
    template_name = 'series_list.html'
    context_object_name = 'series'
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        series = self.get_queryset()
        paginator = Paginator(series, self.paginate_by)
        page = self.request.GET.get('page')
        context['series'] = paginator.get_page(page)
        return context


@login_required
def mark_watched(request, pk):
    movie = get_object_or_404(Movie, pk=pk)
    Watched.objects.create(user=request.user, movie=movie)
    return redirect('movie_detail', pk=pk)


@login_required
def mark_favorite(request, pk):
    movie = get_object_or_404(Movie, pk=pk)
    Favorite.objects.create(user=request.user, movie=movie)
    return redirect('movie_detail', pk=pk)


@login_required
def watched_list(request):
    watched_movies = Watched.objects.filter(user=request.user)
    return render(request, 'watched_list.html', {'watched_movies': watched_movies})


@login_required
def favorite_list(request):
    favorite_movies = Favorite.objects.filter(user=request.user)
    return render(request, 'favorite_list.html', {'favorite_movies': favorite_movies})


@login_required
def movie_detail(request, pk):
    movie = get_object_or_404(Movie, pk=pk)
    is_favorite = Favorite.objects.filter(user=request.user, movie=movie).exists()
    is_watched = Watched.objects.filter(user=request.user, movie=movie).exists()
    context = {
        'movie': movie,
        'is_favorite': is_favorite,
        'is_watched': is_watched,
    }
    return render(request, 'core/movie_detail.html', context)


@login_required
def series_detail(request, pk):
    series = get_object_or_404(Series, pk=pk)
    seasons = series.seasons.all()
    context = {
        'series': series,
        'seasons': seasons,
    }
    return render(request, 'core/series_detail.html', context)


@login_required
def season_detail(request, pk):
    season = get_object_or_404(Season, pk=pk)
    episodes = season.episodes.all()
    context = {
        'season': season,
        'episodes': episodes,
    }
    return render(request, 'core/season_detail.html', context)


@login_required
def episode_detail(request, pk):
    episode = get_object_or_404(Episode, pk=pk)
    context = {
        'episode': episode,
    }
    return render(request, 'core/episode_detail.html', context)


@login_required
def movie_list(request):
    movies = Movie.objects.all()
    context = {
        'movies': movies,
    }
    return render(request, 'core/movie_list.html', context)


@login_required
def series_list(request):
    series = Series.objects.all()
    context = {
        'series': series,
    }
    return render(request, 'core/series_list.html', context)


@login_required
def watched_list(request):
    movies_watched = Watched.objects.filter(user=request.user, movie__isnull=False)
    series_watched = Watched.objects.filter(user=request.user, series__isnull=False)
    context = {
        'movies_watched': movies_watched,
        'series_watched': series_watched,
    }
    return render(request, 'core/watched_list.html', context)


@login_required
def favorite_list(request):
    movies_favorite = Favorite.objects.filter(user=request.user, movie__isnull=False)
    series_favorite = Favorite.objects.filter(user=request.user, series__isnull=False)
    context = {
        'movies_favorite': movies_favorite,
        'series_favorite': series_favorite,
    }
    return render(request, 'core/favorite_list.html', context)


@login_required
def toggle_favorite(request, pk):
    movie = get_object_or_404(Movie, pk=pk)
    favorite, created = Favorite.objects.get


class CategoryList(ListView):
    model = Category
    template_name = 'category_list.html'
    context_object_name = 'categories'


class SeriesDetail(View):
    def get(self, request, *args, **kwargs):
        series = get_object_or_404(Series, pk=kwargs['pk'])
        seasons = Season.objects.filter(series=series).order_by('number')
        return render(request, 'series_detail.html', {
            'series': series,
            'seasons': seasons
        })


class SeasonDetail(DetailView):
    model = Season
    template_name = 'season_detail.html'


class EpisodeDetail(DetailView):
    model = Episode
    template_name = 'episode_detail.html'


class SearchView(ListView):
    model = Movie
    template_name = 'search_results.html'
    context_object_name = 'movies'

    def get_queryset(self):
        query = self.request.GET.get('q')
        category = self.request.GET.get('category')
        if category:
            movies = self.model.objects.filter(title__icontains=query, category__name__icontains=category)
        else:
            movies = self.model.objects.filter(title__icontains=query)
        return movies


@login_required
def search(request):
    query = request.GET.get('q')
    category_name = request.GET.get('category')
    if category_name:
        movies = Movie.objects.filter(title__icontains=query, category__name__icontains=category_name)
        series = Series.objects.filter(title__icontains=query, category__name__icontains=category_name)
    else:
        movies = Movie.objects.filter(title__icontains=query)
        series = Series.objects.filter(title__icontains=query)

    categories = Category.objects.filter(name__icontains=query)

    return render(request, 'search.html', {
        'query': query,
        'movies': movies,
        'series': series,
        'categories': categories,
        'category_name': category_name,
    })


@login_required
def analytics_view(request):
    data = calculate_total_duration()
    # Creamos la gráfica
    fig = make_subplots(rows=1, cols=2, subplot_titles=('Duración total de películas', 'Duración total de series'))

    fig.add_trace(
        go.Bar(x=data.index, y=data['movies_duration'], name='Movie'),
        row=1, col=1
    )
    fig.add_trace(
        go.Bar(x=data.index, y=data['series_duration'], name='Series'),
        row=1, col=2
    )

    fig.update_layout(title='Duración total de películas y series vistas por usuario',
                      xaxis_title='Usuario',
                      yaxis_title='Duración (minutos)',
                      height=500,
                      width=1000)

    # Convertimos la gráfica en HTML para poder mostrarla en la plantilla
    graph = fig.to_html(full_html=False)

    context = {'graph': graph}
    return render(request, 'analytics.html', context)


@login_required
def admin_analytics(request):
    return render(request, 'admin_analytics.html')
