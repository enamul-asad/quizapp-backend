from django.urls import path
from .views import (
    RegisterView, 
    QuizListView, 
    QuizDetailView, 
    SubmitQuizView,
    UserStatsView, 
    ManageUserView, 
    MyTokenObtainPairView,
    ChangePasswordView,
    DeleteAccountView,
    LeaderboardView,
    UserHistoryView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
    AvatarUpdateView

)
from rest_framework_simplejwt.views import TokenRefreshView # pyright: ignore[reportMissingImports]

urlpatterns = [
    # --- Auth ---
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'), # ✅ Uses Custom View
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # --- Profile & Security ---
    path('user/profile/', ManageUserView.as_view(), name='user-profile'),
    path('user/change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('user/delete-account/', DeleteAccountView.as_view(), name='delete-account'),
    path('password-reset/', PasswordResetRequestView.as_view(), name='password-reset-request'),
    path('password-reset/confirm/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),

    # --- Quiz Data ---
    path('quizzes/', QuizListView.as_view(), name='quiz-list'),
    path('quizzes/<int:pk>/', QuizDetailView.as_view(), name='quiz-detail'),
    path('quizzes/<int:pk>/submit/', SubmitQuizView.as_view(), name='quiz-submit'),

    # --- Analytics ---
    path('leaderboard/', LeaderboardView.as_view(), name='leaderboard'),
    path('history/', UserHistoryView.as_view(), name='user-history'),
    path('user/stats/', UserStatsView.as_view(), name='user-stats'),
    path('user/avatar/', AvatarUpdateView.as_view(), name='user-avatar'),
]