from collections import defaultdict

from django.contrib.auth import authenticate
from django.template.context_processors import media
from rest_framework_simplejwt.tokens import RefreshToken
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
# Assuming you have a RegisterSerializer
from .serializers import RegisterSerializer, OpportunitySerializer, OpportunityDisplaySerializer
from .serializers import VoteSerializer, EmailDisplaySerializer, WorkspaceSerializer, IDSerializer
from .serializers import OpportunityResultsSerializer 
from rest_framework.permissions import IsAuthenticated
from .models import Vote, Opportunity, VotingSession, User, Workspace
import numpy as np

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

                # get the most recent voting session
                # mostRecentVotingSession = VotingSession.objects.filter(opportunity=obj.opportunity_id)[0].vs_id
                # temporary for testing
                oppid = obj.opportunity_id
                newD['participants'] = Vote.objects.filter(opportunity=oppid).values('user').distinct().count()
                votes = Vote.objects.filter(opportunity=oppid)
                total = 0
                count = 0
                for vote in votes:
                    total += vote.vote_score
                    count += 1
                newD['score'] = total / count if count != 0 else 0
                opportunities.append(newD)
            serializer = OpportunityDisplaySerializer(opportunities, many=True)
            workspaces.append((ws.name, ws.code, serializer.data))
        
        return Response(workspaces, status=status.HTTP_200_OK)
    
class EmailDisplayView(APIView):
    def get(self, request):
        user = request.user
        serializer = EmailDisplaySerializer(user)
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
    
import random
import string

class WorkspaceCreateView(APIView):
    def post(self, request):
        user = request.user
        code = request.data.get('code')  # Retrieve code from request data
        
        request.data['code'] = code  # Ensure code is set in request data
        request.data['user'] = user.id  # Set the user in request data

        serializer = WorkspaceSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OpportunityCreateView(APIView):
    def post(self, request):
        user = request.user
        request.data['user'] = user.id
        serializer = OpportunitySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
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
            opportunities.append(newD)

        serializer = OpportunityResultsSerializer(data=opportunities, many=True)
        if serializer.is_valid():
            return Response(serializer.data, status=status.HTTP_200_OK)
        print(serializer.errors)
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
    
