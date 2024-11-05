from django.http import HttpResponse
import qrcode
from django.contrib.auth import authenticate
from django.template.context_processors import media
from rest_framework_simplejwt.tokens import RefreshToken
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import RegisterSerializer, OpportunitySerializer, OpportunityDisplaySerializer, VoteSerializer
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
    def post(self, request):
        serializer = OpportunitySerializer(data=request.data)
        if serializer.is_valid():
            # Save the opportunity
            opportunity = serializer.save(user=request.user)

            # Generate the voting session for the new opportunity
            pin_code = generate_unique_pin()

            # Construct the URL with the pin code for the voting session
            url_link = f"{request.build_absolute_uri('/api/voting_session/')}{pin_code}/qr_code/"

            # Create a new voting session with the URL and PIN
            voting_session = VotingSession.objects.create(
                opportunity=opportunity,
                code=pin_code,
                url_link=url_link
            )

            # Generate the QR code for this session URL
            qr_image_path = self.generate_qr_code(url_link, pin_code)

            return Response({
                'opportunity': serializer.data,
                'voting_session': {
                    'pin': pin_code,
                    'url': url_link,
                    'qr_code_path': qr_image_path
                }
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def generate_qr_code(self, url_link, pin_code):
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(url_link)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        
        # Define the path for saving the QR code
        directory = 'qr_codes'
        if not os.path.exists(directory):
            os.makedirs(directory)

        img_path = os.path.join(directory, f"{pin_code}.png")  # Use pin_code for the filename
        img.save(img_path)
        return img_path
    
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
