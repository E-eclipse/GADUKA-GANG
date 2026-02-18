from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from .models import UserProfile, Section, Topic, Post, Tag

User = get_user_model()


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    privacy_policy_accepted = forms.BooleanField(
        required=True,
        label='Я согласен с политикой конфиденциальности',
        error_messages={'required': 'Необходимо принять политику конфиденциальности для регистрации.'}
    )

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['avatar_url', 'bio', 'signature']
        widgets = {
            'avatar_url': forms.URLInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'signature': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class SectionForm(forms.ModelForm):
    """Форма для создания и редактирования разделов"""

    class Meta:
        model = Section
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Название раздела'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Описание раздела'}),
        }


class TopicForm(forms.ModelForm):
    """Форма для создания и редактирования тем"""

    tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label='Теги'
    )

    class Meta:
        model = Topic
        fields = ['title', 'section', 'tags']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Название темы'}),
            'section': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            # При редактировании загружаем существующие теги
            self.fields['tags'].initial = self.instance.topic_tags.all().values_list('tag_id', flat=True)


class PostForm(forms.ModelForm):
    """Форма для создания и редактирования сообщений"""

    class Meta:
        model = Post
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 10,
                'placeholder': 'Напишите ваше сообщение...',
                'id': 'post-content'
            }),
        }
