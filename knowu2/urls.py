from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('game/next_status/', views.game_next_status, name='game_next_status'),
    path('round/reply/', views.round_reply, name='round_reply'),
    path('round/judge/', views.round_judge, name='round_judge'),
    path('round/result/', views.round_result, name='round_result'),
    path('round/next/', views.round_next, name='round_next'),
]
