from django.urls import path
from .views import (
    HealthView, SignupView, LoginView, GuestCreateView, WorkspaceDisplayView,
    SendInviteEmailView, WorkspaceCreateView, WorkspaceByCodeView, GetResults,
    GetID, EmailDisplayView, ChangeEmailView, ChangePasswordView,
    OpportunityCreateView, VoteListView, SubmitVoteView
)
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('health/', HealthView.as_view(), name='health'),
    path('api/signup/', SignupView.as_view(), name='signup'),
    path('api/login/', LoginView.as_view(), name='login'),
    path('api/guests/', GuestCreateView.as_view(), name='guest_create'),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/query/owneropps/', WorkspaceDisplayView.as_view(), name='owner_opp_query'),
    path('api/query/workspace_by_code/', WorkspaceByCodeView.as_view(), name='workspace_by_code'),  # New URL for public workspace data
    path('api/query/oppresults/', GetResults.as_view(), name='opp_results_query'),
    path('api/query/id/', GetID.as_view(), name='id_query'),
    path('api/query/email/', EmailDisplayView.as_view(), name='email_query'),
    path('api/change/email/', ChangeEmailView.as_view(), name='change_email'),
    path('api/change/password/', ChangePasswordView.as_view(), name='change_password'),
    path('api/create_opportunity/', OpportunityCreateView.as_view(), name='create_opportunity'),
    path('api/send_invite_email/', SendInviteEmailView.as_view(), name='send_invite_email'),
    path('api/create_workspace/', WorkspaceCreateView.as_view(), name='create_workspace'),
    path('api/vote_list/', VoteListView.as_view(), name='vote_list'),
    path('api/submit_vote/', SubmitVoteView.as_view(), name='submit_vote'),
]
