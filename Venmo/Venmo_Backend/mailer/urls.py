from django.urls import path

from . import views

urlpatterns = [
    # ── SPA ───────────────────────────────────────────────────────────────
    path('', views.index, name='index'),

    # ── REST API ──────────────────────────────────────────────────────────
    path('api/mail-config/', views.api_mail_config, name='api_mail_config'),
    path('api/send/', views.api_send, name='api_send'),
    path('api/preview/', views.api_preview, name='api_preview'),
    path('api/templates/', views.api_templates, name='api_templates'),
    path('api/templates/<int:pk>/', views.api_template_detail, name='api_template_detail'),
    path('api/logs/', views.api_logs, name='api_logs'),
]
