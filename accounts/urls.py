# accounts/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    RegisterViewSet,
    LoginViewSet,
    LogoutViewSet,
    EmailVerifyViewSet,
    PasswordResetViewSet,
    UserViewSet,   # ProfileViewSet + UsersViewSet o'rniga bitta UserViewSet qilgansan deb tasavvur qilamiz
)

router = DefaultRouter()
router.register(r'', UserViewSet, basename='users')
# natijada:
#   GET  /users/          -> user list (search bilan)
#   GET  /users/{id}/     -> user detail
#   GET  /users/{id}/followers/
#   GET  /users/{id}/following/
#   POST /users/{id}/follow/
#   DELETE /users/{id}/unfollow/
#   GET/PATCH /users/me/  -> current user

urlpatterns = [
    # AUTH endpointlar
    path('auth/register/', RegisterViewSet.as_view({'post': 'create'}), name='auth-register'),
    path('auth/login/',    LoginViewSet.as_view({'post': 'create'}),    name='auth-login'),
    path('auth/logout/',   LogoutViewSet.as_view({'post': 'create'}),   name='auth-logout'),
    path('auth/verify-email/', EmailVerifyViewSet.as_view({'post': 'create'}), name='auth-verify-email'),
    path('auth/password-reset/request/',
         PasswordResetViewSet.as_view({'post': 'request_reset'}), name='auth-password-reset-request'),
    path('auth/password-reset/confirm/',
         PasswordResetViewSet.as_view({'post': 'confirm_reset'}), name='auth-password-reset-confirm'),

    # USER resource router
    path('', include(router.urls)),
]