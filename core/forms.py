from core.models import Profile, Movie
from django.forms import ModelForm
from .models import Category, Series
from django import forms


class ProfileForm(ModelForm):
    class Meta:
        model = Profile
        exclude = ['uuid']


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name']


class MovieForm(forms.ModelForm):
    category = forms.ModelChoiceField(queryset=Category.objects.all())

    class Meta:
        model = Movie
        fields = '__all__'


class SeriesForm(forms.ModelForm):
    category = forms.ModelChoiceField(queryset=Category.objects.all())

    class Meta:
        model = Series
        fields = '__all__'
