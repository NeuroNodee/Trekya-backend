from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    RegisterView,
    LoginView,
    LogoutView,
    UserDetailView,
    change_password,
    reset_password,
    send_otp,
    send_otpV2,
    verify_otp,
    GoogleLogin,
    FacebookLogin,
)

urlpatterns = [
    # Authentication endpoints
    path('signup/', RegisterView.as_view(), name='signup'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('google/', GoogleLogin.as_view(), name='google_login'),
    path('facebook/', FacebookLogin.as_view(), name='facebook_login'),
    
    # Token management
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # User management
    path('user/', UserDetailView.as_view(), name='user-detail'),
    path('change-password/', change_password, name='change-password'),
    path('reset-password/', reset_password, name='reset-password'),
    path('send-otp/', send_otp, name='send-otp'),
    path('send-otpV2/', send_otpV2, name='send-otpV2'),
    path('verify-otp/', verify_otp, name='verify-otp'),
]