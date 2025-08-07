from django.urls import path
from dashboard.views import dashboard,problem_detail,leaderboard_view
from . import views
from sign_up.views import login_user

urlpatterns = [
    path("", dashboard, name="dashboard"),
    path("problem/<int:id>", problem_detail, name="problem_detail"),
    path('leaderboard/', leaderboard_view, name='leaderboard'),
    path('profile/<str:username>/', views.profile_view, name='profile'),
    path('favorite/toggle/<int:question_id>/', views.toggle_favorite, name='toggle_favorite'),
    path('favorites/', views.favorite_list_view, name='favorite_list'),
    
    
]


