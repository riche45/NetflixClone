import pandas as pd
from core.models import Watched
import matplotlib.pyplot as plt


def get_watched_data():
    data = Watched.objects.all().values_list('user_id', 'movie__duration', 'series__total_duration', 'created_at')
    df = pd.DataFrame(list(data), columns=['user_id', 'movie_duration', 'series_duration', 'created_at'])
    return df


def calculate_total_duration():
    df = get_watched_data()
    total_duration = df.groupby('user_id').agg(
        movies_duration=('movie_duration', 'sum'),
        series_duration=('series_duration', 'sum')
    )
    return total_duration


def plot_total_duration():
    total_duration = calculate_total_duration()
    total_duration.plot(kind='bar')
    plt.title('Duración total de películas y series vistas por usuario')
    plt.xlabel('Usuario')
    plt.ylabel('Duración (minutos)')
    plt.show()


if __name__ == '__main__':
    plot_total_duration()
