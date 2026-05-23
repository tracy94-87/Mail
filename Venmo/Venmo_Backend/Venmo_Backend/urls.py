from django.urls import path, include

urlpatterns = [
    path('', include('mailer.urls')),
]
