
from .serializers import GuestSerializer
from rest_framework import status
from django.http import HttpResponse
from collections import defaultdict
from django.contrib.auth import authenticate
from django.template.context_processors import media
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .serializers import *
from rest_framework.permissions import IsAuthenticated
from .models import *
import numpy as np
import random
import uuid
from django_ratelimit.decorators import ratelimit

# Utility function to generate tokens for a user

def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

# Health check endpoint (optional)


class HealthView(APIView):
    def get(self, request):
        response = {'message': 'hello world'}
        return Response(response, status=status.HTTP_200_OK)

# Signup view to register new users and issue JWT tokens
class SignupView(APIView):
    def post(self, request, *args, **kwargs):
        # Log incoming request data
        print("Received request data:", request.data)

        serializer = RegisterSerializer(data=request.data)

        if serializer.is_valid():
            print("Serializer valid")
            user = serializer.save()
            print("User created:", user)

            tokens = get_tokens_for_user(user)
            return Response({
                'message': 'User registered successfully',
                'tokens': tokens
            }, status=status.HTTP_201_CREATED)

        print("Serializer errors:", serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class GuestCreateView(APIView):
    permission_classes = []  # Allow all users

    def post(self, request):
        serializer = GuestSerializer(data=request.data)
        if serializer.is_valid():
            guest = serializer.save()
            return Response({'guest_id': guest.guest_id}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    def post(self, request, *args, **kwargs):
        # Extract email and password from the request
        email = request.data.get('email')
        password = request.data.get('password')

        # Authenticate user
        user = authenticate(request, username=email, password=password)

        if user is not None:
            # Generate tokens if authentication is successful
            tokens = get_tokens_for_user(user)
            return Response({
                'message': 'Login successful',
                'tokens': tokens,
            }, status=status.HTTP_200_OK)
        else:
            # Authentication failed
            return Response({'error': 'Invalid email or password'}, status=status.HTTP_401_UNAUTHORIZED)

'''
class WorkspaceDisplayView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        code = request.query_params.get("code")  # Get the code from the query parameters

        if not code:
            return Response({"error": "Code is required"}, status=status.HTTP_400_BAD_REQUEST)

        # Filter the workspace by `code` and `user_id` (to get only workspaces owned by the user)
        wss = Workspace.objects.filter(code=code, user_id=request.user.id)
        if not wss.exists():
            return Response({"error": "Workspace not found"}, status=status.HTTP_404_NOT_FOUND)

        workspaces = []
        for ws in wss:
            # Retrieve opportunities associated with the workspace
            os = Opportunity.objects.filter(workspace=ws.workspace_id)
            opportunities = []

            for obj in os:
                newD = {
                    "name": obj.name,
                    "customer_segment": obj.customer_segment,
                    "label": obj.status if obj.status is not None else "TBD",
                    "participants": Vote.objects.filter(opportunity=obj.opportunity_id).values('user').distinct().count(),
                }
                
                # Calculate average score for the opportunity
                votes = Vote.objects.filter(opportunity=obj.opportunity_id)
                total_score = sum(vote.vote_score for vote in votes)
                vote_count = votes.count()
                newD["score"] = total_score / vote_count if vote_count > 0 else 0
                opportunities.append(newD)

            # Serialize opportunity data
            serializer = OpportunityDisplaySerializer(opportunities, many=True)
            workspaces.append({
                "name": ws.name,
                "url_link": ws.url_link,
                "opportunities": serializer.data
            })

        # Return all relevant workspaces (though this will usually just be one workspace due to `code` filter)
        return Response(workspaces, status=status.HTTP_200_OK)
'''

class WorkspaceByCodeView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        code = request.query_params.get("code")
        if not code:
            return Response({"error": "Code is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            ws = Workspace.objects.get(code=code)
        except Workspace.DoesNotExist:
            return Response({"error": "Workspace not found"}, status=status.HTTP_404_NOT_FOUND)

        # Prepare workspace data
        data = {
            "name": ws.name,
            "url_link": ws.url_link,
        }

        return Response(data, status=status.HTTP_200_OK)
    

class WorkspaceCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        request.data['user'] = user.id  # Set the user in request data

        serializer = WorkspaceSerializer(data=request.data)
        if serializer.is_valid():
            workspace = serializer.save()

            # Generate a unique session pin if not already set
            if not workspace.code:
                workspace.code = workspace.generate_unique_code()
                workspace.save(update_fields=['code'])

            return Response({
                'workspace_id': workspace.workspace_id,
                'name': workspace.name,
                'code': workspace.code,
                'url_link': workspace.url_link,
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


'''
class WorkspaceCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = WorkspaceSerializer(data=request.data)
        if serializer.is_valid():
            workspace = serializer.save(user=request.user)
            # Create the voting session associated with the workspace
            pin_code = workspace.code
            protocol = 'https' if request.is_secure() else 'http'
            domain = request.get_host()
            url_link = f"{protocol}://{domain}/voting/{pin_code}"

            workspace.url_link = url_link
            workspace.save(update_fields=['url_link'])

            VotingSession.objects.create(
                workspace=workspace,
                code=pin_code,
                url_link=url_link,
                start_time=timezone.now(),
                end_time=None,
            )

            # No need to generate QR code here, since we will generate it on the frontend

            return Response({
                'workspace_id': workspace.workspace_id,
                'name': workspace.name,
                'code': workspace.code,
                'url_link': workspace.url_link,
                'voting_session': {
                    'pin': pin_code,
                    'url_link': url_link,
                }
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
'''
        
class WorkspaceDisplayView(APIView):
    def get(self, request):
        user = request.user
        wss = Workspace.objects.filter(user_id=user.id)
        workspaces = []
        for ws in wss:
            os = Opportunity.objects.filter(workspace=ws.workspace_id)
            opportunities = []
            for obj in os:
                newD = {}
                newD['name'] = obj.name
                newD['customer_segment']= obj.customer_segment
                newD['label'] = obj.status if obj.status != None else "TBD"

                # temporary for testing
                oppid = obj.opportunity_id
                newD['participants'] = Vote.objects.filter(opportunity=oppid).values('user').distinct().count()
                votes = Vote.objects.filter(opportunity=oppid)
                totalP = 0
                countP = 0
                totalC = 0
                countC = 0
                for vote in votes:
                    if vote.criteria_id <= 3:
                        totalP += vote.vote_score
                        countP += 1
                    else:
                        totalC += vote.vote_score
                        countC += 1
                newD['scoreP'] = totalP / countP if countP != 0 else 0
                newD['scoreC'] = totalC / countC if countC != 0 else 0
                opportunities.append(newD)
            serializer = OpportunityDisplaySerializer(opportunities, many=True)
            workspaces.append((ws.name, ws.code, serializer.data))
        
        return Response(workspaces, status=status.HTTP_200_OK)
    
class EmailDisplayView(APIView):
    def get(self, request):
        user = request.user
        serializer = EmailDisplaySerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class AddReasonView(APIView):
    def post(self, request):
        reason = request.data.get('reason')
        criteria_id = request.data.get('criteria_id')
        opportunity_id = request.data.get('opportunity_id')
        user = request.user
        v = Vote.objects.filter(user=user.id, criteria_id=criteria_id, opportunity=opportunity_id)[0]
        v.user_vote_explanation = reason
        v.save()
        return Response({}, status=status.HTTP_200_OK)

class ChangeEmailView(APIView):
    def post(self, request):
        newEmail = request.data.get('newEmail')
        user = request.user
        try:
            user.username = newEmail
            user.email = newEmail
            user.save()
        except:
            return Response({'message': 'Email may aleady be in use'}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        return Response({}, status=status.HTTP_200_OK)


class ChangePasswordView(APIView):
    def post(self, request):
        user = request.user
        password = request.data.get('currentPassword')
        newPassword = request.data.get('newPassword')
        confirmNewPassword = request.data.get('confirmNewPassword')
        if newPassword != confirmNewPassword:
            return Response({'message': 'Passwords do not match'}, status=status.HTTP_400_BAD_REQUEST)
        user = authenticate(request, username=user.email, password=password)
        if user is None:
            # Authentication failed
            return Response({'message': 'Unable to authorize'}, status=status.HTTP_401_UNAUTHORIZED)
        user.set_password(newPassword)
        user.save()
        return Response({}, status=status.HTTP_200_OK)  


class OpportunityCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request):
        serializer = OpportunitySerializer(data=request.data)
        if serializer.is_valid():
            opportunity = serializer.save(user=request.user)
            return Response({'opportunity': serializer.data}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SendInviteEmailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        recipient_email = request.data.get('email')
        workspace_id = request.data.get('workspace_id')

        if not recipient_email or not workspace_id:
            return Response({'error': 'Email and workspace_id are required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            workspace = Workspace.objects.get(pk=workspace_id)
            if workspace.user != request.user:
                return Response({'error': 'You are not the owner of this workspace'}, status=status.HTTP_403_FORBIDDEN)

            # Generate unique token for the invitation
            token = uuid.uuid4()

            # Create invitation
            invitation = Invitation.objects.create(
                workspace=workspace,
                email=recipient_email,
                token=token,
            )

            # Generate invite link with token
            protocol = 'https' if request.is_secure() else 'http'
            domain = request.get_host()
            invite_link = f"{protocol}://{domain}/join/{token}/"

            # Compose email
            subject = 'You are invited to a voting session'
            message = f"Please join the voting session using the following link: {
                invite_link}"
            from_email = settings.DEFAULT_FROM_EMAIL
            recipient_list = [recipient_email]

            # Send email
            send_mail(subject, message, from_email, recipient_list)

            return Response({'message': 'Invite email sent successfully'}, status=status.HTTP_200_OK)
        except Workspace.DoesNotExist:
            return Response({'error': 'Workspace not found'}, status=status.HTTP_400_BAD_REQUEST)


# Same as results for now, shoudl change for security later    
class GetVoting(APIView):
    def get(self, request):
        user = request.user
        session = request.query_params.get('code')
        ws = Workspace.objects.filter(code=session)[0]
        os = Opportunity.objects.filter(workspace=ws.workspace_id)

        opportunities = []
        for obj in os:
            newD = {}
            reasons = ['' for i in range(6)]
            oppid = obj.opportunity_id
            vs = Vote.objects.filter(opportunity=oppid)
            cur_votes = [ [0]*5 for i in range(6)]
            for v in vs:
                cur_votes[v.criteria_id - 1][v.vote_score - 1]+=1
                if v.user_vote_explanation != None:
                    if reasons[v.criteria_id - 1] != "":
                        reasons[v.criteria_id - 1] += '; '
                    reasons[v.criteria_id - 1] += 'Vote=' + str(v.vote_score) + ': ' + v.user_vote_explanation
            newD['name'] = obj.name
            newD['customer_segment'] = obj.customer_segment
            newD['description'] = obj.description
            newD['opportunity_id'] = obj.opportunity_id
            for i in range(6):
                if reasons[i] == '':
                    reasons[i] = 'No outliers'
            newD['reasons'] = reasons
            newD['imgurl'] = obj.image.url if obj.image != None else '../../wtp.png'
            opportunities.append(newD)

        serializer = OpportunityVotingSerializer(data=opportunities, many=True)
        if serializer.is_valid():
            return Response(serializer.data, status=status.HTTP_200_OK)
        print(serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GetResults(APIView):
    def get(self, request):
        user = request.user
        session = request.query_params.get('code')
        try:
            ws = Workspace.objects.filter(code=session)[0]
            if user.id != ws.user.id:
                 return Response({'message': "You are not the owner"}, status=status.HTTP_403_FORBIDDEN)
            os = Opportunity.objects.filter(workspace=ws.workspace_id)
        except:
            return Response({'message': f"No workspace with session code {session}"}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        

        opportunities = []
        for obj in os:
            newD = {}
            reasons = ['' for i in range(6)]
            oppid = obj.opportunity_id
            vs = Vote.objects.filter(opportunity=oppid)
            cur_votes = [ [0]*5 for i in range(6)]
            for v in vs:
                cur_votes[v.criteria_id - 1][v.vote_score - 1]+=1
                if v.user_vote_explanation != None:
                    if reasons[v.criteria_id - 1] != "":
                        reasons[v.criteria_id - 1] += '; '
                    reasons[v.criteria_id - 1] += 'Vote=' + str(v.vote_score) + ': ' + v.user_vote_explanation
            newD['name'] = obj.name
            newD['customer_segment'] = obj.customer_segment
            newD['description'] = obj.description
            newD['cur_votes'] = cur_votes
            for i in range(6):
                if reasons[i] == '':
                    reasons[i] = 'No outliers'
            newD['reasons'] = reasons
            newD['imgurl'] = obj.image.url if obj.image != None else '../../wtp.png'
            opportunities.append(newD)

        serializer = OpportunityResultsSerializer(data=opportunities, many=True)
        if serializer.is_valid():
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)             
                
    
class GetID(APIView):
    def get(self, request):
        user = request.user
        dataa = {}
        dataa['id'] = user.id
        serializer = IDSerializer(data=dataa)
        if serializer.is_valid():
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class GetResults(APIView):
    def get(self, request):
        user = request.user
        session = request.query_params.get('code')
        try:
            ws = Workspace.objects.filter(code=session)[0]
            if user.id != ws.user.id:
                 return Response({'message': "You are not the owner"}, status=status.HTTP_403_FORBIDDEN)
            os = Opportunity.objects.filter(workspace=ws.workspace_id)
        except:
            return Response({'message': f"No workspace with session code {session}"}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        

        opportunities = []
        for obj in os:
            newD = {}
            reasons = ['' for i in range(6)]
            oppid = obj.opportunity_id
            vs = Vote.objects.filter(opportunity=oppid)
            cur_votes = [ [0]*5 for i in range(6)]
            for v in vs:
                cur_votes[v.criteria_id - 1][v.vote_score - 1]+=1
                if v.user_vote_explanation != None:
                    if reasons[v.criteria_id - 1] != "":
                        reasons[v.criteria_id - 1] += '; '
                    reasons[v.criteria_id - 1] += 'Vote=' + str(v.vote_score) + ': ' + v.user_vote_explanation
            newD['name'] = obj.name
            newD['customer_segment'] = obj.customer_segment
            newD['description'] = obj.description
            newD['cur_votes'] = cur_votes
            for i in range(6):
                if reasons[i] == '':
                    reasons[i] = 'No outliers'
            newD['reasons'] = reasons
            newD['imgurl'] = obj.image.url if obj.image != None else '../../wtp.png'
            print(newD)
            opportunities.append(newD)

        serializer = OpportunityResultsSerializer(data=opportunities, many=True)
        if serializer.is_valid():
            return Response(serializer.data, status=status.HTTP_200_OK)
        print(serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)    

class CreateReason(APIView):
    def post(self, request):
        pass    


class DeleteUser(APIView):  
    def post(self, request):
        try:
            user = request.user
            user.delete()
            return Response({}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': e.message}, status=status.HTTP_400_BAD_REQUEST)
                


    
class GetID(APIView):
    def get(self, request):
        user = request.user
        dataa = {}
        dataa['id'] = user.id
        serializer = IDSerializer(data=dataa)
        if serializer.is_valid():
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SubmitVoteView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        data = request.data.copy()
        user = request.user if request.user.is_authenticated else None
        guest_id = data.get('guest_id')

        if not user and not guest_id:
            return Response({'error': 'Authentication required.'}, status=status.HTTP_401_UNAUTHORIZED)

        if guest_id:
            try:
                guest = Guest.objects.get(pk=guest_id)
            except Guest.DoesNotExist:
                return Response({'error': 'Invalid guest ID.'}, status=status.HTTP_400_BAD_REQUEST)
            data['guest'] = guest_id
        else:
            data['user'] = user.id

        serializer = VoteSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Vote submitted'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


def mad_outlier_detection(data: list, threshold=2):

    median = np.median(data)
    abs_deviation = np.abs(data - median)
    mad = np.median(abs_deviation)
    lower_limit = median-(threshold*mad)
    upper_limit = median+(threshold*mad)
    outliers = []
    for i in data:
        if i < lower_limit or i > upper_limit:
            outliers.append(i)
    if not outliers:
        outliers.append("No outliers detected")
    return outliers


class VoteListView(APIView):

    def get(self, request):
        queryset = Vote.objects.all()
        if queryset.exists():
            serializer = VoteSerializer(queryset, many=True)
            data = serializer.data
            grouped_scores = defaultdict(list)
            score_list = []
            for item in data:
                grouped_scores[item['criteria_id']].append(item["vote_score"])
            for criteria_id, vote_score in grouped_scores.items():
                print(f'Criteria ID: {criteria_id}: {vote_score}, Outliers: {mad_outlier_detection(vote_score)}')
            return Response(data, status=status.HTTP_200_OK)
        return Response({'error': 'No votes found'}, status=status.HTTP_400_BAD_REQUEST)
    

class JoinWorkspaceView(APIView):
    permission_classes = [permissions.AllowAny]

    @ratelimit(key='ip', rate='10/m', block=True)
    def get(self, request, token):
        try:
            invitation = Invitation.objects.get(token=token)
            workspace = invitation.workspace

            if invitation.accepted_at:
                return Response({'error': 'This invitation link has already been used.'}, status=status.HTTP_400_BAD_REQUEST)

            data = {
                'workspace_name': workspace.name,
                'workspace_id': workspace.workspace_id,
                'invitation_token': str(token),
            }
            return Response(data, status=status.HTTP_200_OK)
        except Invitation.DoesNotExist:
            return Response({'error': 'Invalid invitation link.'}, status=status.HTTP_400_BAD_REQUEST)

    @ratelimit(key='ip', rate='10/m', block=True)
    def post(self, request, token):
        first_name = request.data.get('first_name')
        last_name = request.data.get('last_name')
        email = request.data.get('email')

        if not first_name or not email:
            return Response({'error': 'First name and email are required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            invitation = Invitation.objects.get(token=token)
            workspace = invitation.workspace

            if invitation.accepted_at:
                return Response({'error': 'This invitation link has already been used.'}, status=status.HTTP_400_BAD_REQUEST)

            # Check guest cap
            current_guest_count = SessionParticipant.objects.filter(
                voting_session=workspace.voting_sessions.last(),
                guest__isnull=False
            ).count()
            if workspace.guest_cap > 0 and current_guest_count >= workspace.guest_cap:
                return Response({'error': 'The guest limit for this workspace has been reached.'}, status=status.HTTP_403_FORBIDDEN)

            # Create Guest object
            guest, created = Guest.objects.get_or_create(
                email=email,
                defaults={'first_name': first_name, 'last_name': last_name}
            )

            # Associate guest with invitation
            invitation.guest = guest
            invitation.accepted_at = timezone.now()
            invitation.save()

            # Add guest to session participants
            session_participant, created = SessionParticipant.objects.get_or_create(
                voting_session=workspace.voting_sessions.last(),
                guest=guest
            )

            return Response({'message': 'Successfully joined the workspace.'}, status=status.HTTP_200_OK)
        except Invitation.DoesNotExist:
            return Response({'error': 'Invalid invitation link.'}, status=status.HTTP_400_BAD_REQUEST)


class KickParticipantView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        workspace_id = request.data.get('workspace_id')
        participant_id = request.data.get('participant_id')

        try:
            workspace = Workspace.objects.get(pk=workspace_id)
            if workspace.user != request.user:
                return Response({'error': 'You are not the owner of this workspace'}, status=status.HTTP_403_FORBIDDEN)

            participant = SessionParticipant.objects.get(pk=participant_id)
            participant.delete()

            return Response({'message': 'Participant kicked successfully'}, status=status.HTTP_200_OK)
        except Workspace.DoesNotExist:
            return Response({'error': 'Workspace not found'}, status=status.HTTP_400_BAD_REQUEST)
        except SessionParticipant.DoesNotExist:
            return Response({'error': 'Participant not found'}, status=status.HTTP_400_BAD_REQUEST)

class GuestJoinSessionView(APIView):
    permission_classes = []  # Allow unauthenticated access

    def post(self, request):
        session_pin = request.data.get('sessionPin')
        first_name = request.data.get('first_name')
        last_name = request.data.get('last_name')
        email = request.data.get('email')

        if not session_pin or not first_name or not email:
            return Response({"error": "Missing required fields"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Validate session pin by looking up the Workspace
            workspace = Workspace.objects.get(code=session_pin)
        except Workspace.DoesNotExist:
            return Response({"error": "Invalid session pin"}, status=status.HTTP_404_NOT_FOUND)

        # Create or retrieve guest
        guest, created = Guest.objects.get_or_create(
            email=email,
            defaults={'first_name': first_name, 'last_name': last_name}
        )

        # Associate guest with the workspace
        # Assuming there's a ManyToManyField in Workspace for guests
        # e.g., Workspace.guests = models.ManyToManyField(Guest, related_name='workspaces')
        workspace.sessionparticipant_set.get_or_create(guest=guest)

        return Response({"guest_id": guest.guest_id}, status=status.HTTP_201_CREATED)
