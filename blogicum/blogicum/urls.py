from django.contrib import admin
from django.contrib.auth.forms import UserCreationForm
from django.urls import include, path, reverse_lazy
from django.views.generic import CreateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/', include('django.contrib.auth.urls')),
    path(
        'auth/registration/',
        CreateView.as_view(
            template_name='registration/registration_form.html',
            form_class=UserCreationForm,
            success_url=reverse_lazy('pages:index'),
        ),
        name='registration'
    ),
    path('pages/', include('pages.urls')),
    path('', include('blog.urls')),
]

handler404 = 'pages.views.page_not_found'
handler500 = 'pages.views.server_error'
