from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('profile/', views.profile, name='profile'),
    path('leaderboard/', views.leaderboard, name='leaderboard'),
    path('quiz/', views.quiz, name='quiz'),
    path('topics/', views.topics, name='topics'),
    path('result/', views.result, name='result'),
    path('logout/', views.logout_view, name='logout'),
    path('about/', views.about, name='about'),
    path('increment_quiz_played/', views.increment_quiz_played, name='increment_quiz_played'),
    path('update_quiz_results/', views.update_quiz_results, name='update_quiz_results'),
    
    
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

