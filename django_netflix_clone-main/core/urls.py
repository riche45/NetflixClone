
from django.urls import path

from core import views
from core.views import (
    Home,
    ProfileList,
    ProfileCreate,
    Watch,
    MovieCreate,
    SeriesCreate,
    ShowMovieDetail,
    ShowMovie,
    MovieListView,
    SeriesListView,
)

app_name = 'core'

urlpatterns = [
    path('', Home.as_view(), name='index'),
    path('profile/', ProfileList.as_view(), name='profile_list'),
    path('profile/create/', ProfileCreate.as_view(), name='profileCreate'),
    path('watch/<str:profile_id>/', Watch.as_view(), name='watch'),
    path('movie/detail/<str:movie_id>/', ShowMovieDetail.as_view(), name='show_det'),
    path('movie/play/<str:movie_id>/', ShowMovie.as_view(), name='play'),
    path('movie/create/', MovieCreate.as_view(), name='movieCreate'),
    path('movie/list/', MovieListView.as_view(), name='movieList'),
    path('series/create/', SeriesCreate.as_view(), name='seriesCreate'),
    path('series/list/', SeriesListView.as_view(), name='series_list'),
    path('watched/', views.watched_list, name='watched_list'),
    path('favorites/', views.favorite_list, name='favorite_list'),
    path('series/', views.CategoryList.as_view(), name='category_list'),
    path('categories/create/', views.CategoryCreate.as_view(), name='categoryCreate'),
    path('categories/', views.CategoryList.as_view(), name='category_list_create'),
    path('series/<int:pk>/', views.series_detail, name='series_detail'),
    path('seasons/<int:pk>/', views.season_detail, name='season_detail'),
    path('episodes/<int:pk>/', views.episode_detail, name='episode_detail'),
    path('toggle_favorite/<int:pk>/', views.toggle_favorite, name='toggle_favorite'),
    path('search/', views.SearchView.as_view(), name='search'),
    path('search/', views.search, name='search'),
    path('admin_analytics/', views.admin_analytics, name='admin_analytics'),
]
