from django.urls import path
from compile.views import submit_compile

urlpatterns = [
    path("", submit_compile, name="submit"),
]