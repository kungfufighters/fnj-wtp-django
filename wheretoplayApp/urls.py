from django.urls import path
from .views import *
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('health/', HealthView.as_view(), name='health'),
    path('api/signup/', SignupView.as_view(), name='signup'),
    path('api/login/', LoginView.as_view(), name='login'),
    path('api/guests/', GuestCreateView.as_view(), name='guest_create'),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/query/owneropps/', OpportunityDisplayView.as_view(), name='owner_opp_query'),
    path('api/change/email/', ChangeEmailView.as_view(), name='owner_opp_query'),
    path('api/change/password/', ChangePasswordView.as_view(), name='owner_opp_query'),
    path('api/create_opportunity/', OpportunityCreateView.as_view(), name='create_opportunity'),
    path('api/send_invite_email/', SendInviteEmailView.as_view(), name='send_invite_email'),
    path('api/create_workspace/', WorkspaceCreateView.as_view(), name='create_workspace'),
    path('api/vote_list/', VoteListView.as_view(), name='vote_list'),
    path('api/submit_vote/', SubmitVoteView.as_view(), name='submit_vote'),
    path('api/opportunity/<int:id>/', OpportunityDisplayView.as_view(), name='opportunity_detail'),
    path('api/voting_session/<str:pin_code>/', VotingSessionDetailView.as_view(), name='voting_session_detail'),
]