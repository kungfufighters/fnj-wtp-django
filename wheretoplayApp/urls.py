from django.urls import path, include
from .views import *
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView

urlpatterns = [
    path('health/', HealthView.as_view(), name='health'),
    path('api/signup/', SignupView.as_view(), name='signup'),
    path('api/login/', LoginView.as_view(), name='login'),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('api/query/owneropps/', WorkspaceDisplayView.as_view(), name='owner_opp_query'),
    path('api/query/workspace_by_code/', WorkspaceByCodeView.as_view(), name='workspace_by_code'), 
    path('api/query/oppresults/', GetResults.as_view(), name='opp_results_query'),
    path('api/query/oppvoting/', GetVoting.as_view(), name='opp_voting_query'),
    path('api/query/change_vote/', CreateReason.as_view(), name='create_reason'),
    path('api/query/id/', GetID.as_view(), name='id_query'),
    path('api/query/email/', EmailDisplayView.as_view(), name='email_query'),
    path('api/add/reason/', AddReasonView.as_view(), name='reason_add'),
    path('api/change/email/', ChangeEmailView.as_view(), name='email_change'),
    path('api/change/password/', ChangePasswordView.as_view(), name='password_change'),
    path('api/create_opportunity/', OpportunityCreateView.as_view(), name='create_opportunity'),
    path('api/create_workspace/', WorkspaceCreateView.as_view(), name='create_workspace'),
    path('api/vote_list/', VoteListView.as_view(), name='vote_list'),
    path('api/delete_user/', DeleteUser.as_view(), name='delete_user'),
    path('api/submit_vote/', SubmitVoteView.as_view(), name='submit_vote'),
    path('api/send_invite_email/', SendInviteEmailView.as_view(), name='send_invite_email'),
    path('join/<uuid:token>/', JoinWorkspaceView.as_view(), name='join_workspace'),
    path('api/kick_participant/', KickParticipantView.as_view(),
         name='kick_participant'),
    path('api/guests/', GuestJoinSessionView.as_view(), name='guest_join_session'),
    path('api/send_reset_email/', ResetPasswordSendView.as_view(), name='send_reset_email'),
    path('api/reset_password/', ResetPasswordView.as_view(), name='reset_password'),
]
