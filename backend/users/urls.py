from django.urls import path
from .views import RegisterView, LoginView, LogoutView, UserView, CSRFTokenView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('user/', UserView.as_view(), name='user-info'),
    path('csrf/', CSRFTokenView.as_view(), name='csrf-token'),
]
