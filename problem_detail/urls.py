from django.urls import path
from . import views


urlpatterns = [
    
    path('submit/',views.submit,name='submit_question'),
    path('history/<int:question_id>/', views.submission_history_view, name='submission_history'),

]   


