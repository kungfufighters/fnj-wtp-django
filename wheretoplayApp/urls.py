from django.urls import path, include
from .views import *
# from .views import OpportunityView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('health/', HealthView.as_view(), name='health'),
    path('api/signup/', SignupView.as_view(), name='signup'),
    path('api/login/', LoginView.as_view(), name='login'),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/query/owneropps/', OpportunityDisplayView.as_view(), name='owner_opp_query'),
    path('api/query/email/', EmailDisplayView.as_view(), name='owner_opp_query'),
    path('api/change/email/', ChangeEmailView.as_view(), name='owner_opp_query'),
    path('api/change/password/', ChangePasswordView.as_view(), name='owner_opp_query'),
    path('api/create_opportunity/', OpportunityCreateView.as_view(), name='create_opportunity'),
    path('api/create_workspace/', WorkspaceCreateView.as_view(), name='create_workspace'),
    path('api/vote_list/', VoteListView.as_view(), name='vote_list'),
]