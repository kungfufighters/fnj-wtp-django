from django.http import HttpResponse
import qrcode
from django.contrib.auth import authenticate
from django.template.context_processors import media
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
import os

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
        

class WorkspaceCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = WorkspaceSerializer(data=request.data)
        if serializer.is_valid():
            workspace = serializer.save(user=request.user)
            return Response({
                'workspace_id': workspace.workspace_id,
                'name': workspace.name,
                'code': workspace.code 
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class OpportunityDisplayView(APIView):
    def get(self, request):
        user = request.user
        qs = Opportunity.objects.select_related('status').filter(user_id=user.id)

        toReturn = []
        for obj in qs:
            newD = {}
            newD['name'] = obj.name
            newD['customer_segment']= obj.customer_segment
            newD['label'] = obj.status.label
            newD['participants'] = Vote.objects.filter(voting_session=5).values('user').distinct().count()
            toReturn.append(newD)
        
        serializer = OpportunityDisplaySerializer(toReturn, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

'''
class OtherOpportunityView(APIView):
    def get(self, request):
'''  

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


def generate_unique_pin():
    """Generate a unique 5-digit PIN."""
    while True:
        pin = f"{random.randint(10000, 99999)}"
        if not VotingSession.objects.filter(code=pin).exists():
            return pin


class OpportunityCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = OpportunitySerializer(data=request.data)
        if serializer.is_valid():
            opportunity = serializer.save(user=request.user)
            # Retrieve the voting session associated with the opportunity
            voting_session = opportunity.votingsession_set.first()

            if voting_session:
                protocol = 'https' if request.is_secure() else 'http'
                domain = request.get_host()

                # Build the QR code URL
                qr_code_url = f"{protocol}://{domain}/media/qr_codes/{voting_session.code}.png"

                # Prepare response data
                return Response({
                    'opportunity': serializer.data,
                    'voting_session': {
                        'pin': voting_session.code,
                        'url_link': voting_session.url_link,
                        'qr_code_url': qr_code_url
                    }
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({'error': 'Voting session not created'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    
class VotingSessionQRCodeView(APIView):
    def get(self, request, pin):
        try:
            # Retrieve the voting session by PIN code
            voting_session = VotingSession.objects.get(code=pin)
            url = voting_session.url_link

            # Generate the QR code
            qr = qrcode.make(url)
            response = HttpResponse(content_type="image/png")
            qr.save(response, "PNG")
            return response

        except VotingSession.DoesNotExist:
            return Response({"error": "Voting session not found."}, status=status.HTTP_404_NOT_FOUND)


class VotingSessionDetailView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, pin_code):
        try:
            voting_session = VotingSession.objects.get(code=pin_code)
            protocol = 'https' if request.is_secure() else 'http'
            domain = request.get_host()

            # Build the QR code URL
            qr_code_url = f"{protocol}://{domain}/media/qr_codes/{voting_session.code}.png"

            data = {
                'voting_session': {
                    'code': voting_session.code,
                    'url_link': voting_session.url_link,
                    'qr_code_url': qr_code_url,
                    'opportunity_name': voting_session.opportunity.name,
                    'opportunity_description': voting_session.opportunity.description,
                    # Add any other details you need
                }
            }
            return Response(data, status=status.HTTP_200_OK)
        except VotingSession.DoesNotExist:
            return Response({'error': 'Voting session not found'}, status=status.HTTP_404_NOT_FOUND)


class SendInviteEmailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        recipient_email = request.data.get('email')
        pin_code = request.data.get('pin_code')

        if not recipient_email or not pin_code:
            return Response({'error': 'Email and pin_code are required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            voting_session = VotingSession.objects.get(code=pin_code)
            protocol = 'https' if request.is_secure() else 'http'
            domain = request.get_host()
            invite_link = f"{protocol}://{domain}/voting/{pin_code}"

            # Compose email
            subject = 'You are invited to a voting session'
            message = f"Please join the voting session using the following link: {invite_link}"
            from_email = settings.DEFAULT_FROM_EMAIL
            recipient_list = [recipient_email]

            # Send email
            send_mail(subject, message, from_email, recipient_list)

            return Response({'message': 'Invite email sent successfully'}, status=status.HTTP_200_OK)
        except VotingSession.DoesNotExist:
            return Response({'error': 'Voting session not found'}, status=status.HTTP_404_NOT_FOUND)


class SubmitVoteView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        data = request.data.copy()
        if request.user.is_authenticated:
            data['user'] = request.user.id
        else:
            guest_id = request.data.get('guest_id')
            if not guest_id:
                return Response({'error': 'Guest ID is required'}, status=status.HTTP_400_BAD_REQUEST)
            data['guest'] = guest_id

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
        else:
            pass
    return outliers


class VoteListView(APIView):

    def get(self, request):
        queryset = Vote.objects.all()
        if queryset.exists():
            serializer = VoteSerializer(queryset, many=True)
            data = serializer.data
            score_list = []
            for vote in data:
                score = vote.get('vote_score')
                score_list.append(score)
            outliers = mad_outlier_detection(score_list)
            print(f'Users votes for Criteria 1: {score_list}')
            print(f'Outliers using MAD: {outliers}')
            return Response(data, status=status.HTTP_200_OK)
        return Response({'error': 'No votes found'}, status=status.HTTP_400_BAD_REQUEST)
