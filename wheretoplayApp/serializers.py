from .models import Guest
from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from .models import *

'''
class DynamicFieldsModelSerializer(serializers.ModelSerializer):
    """
    A ModelSerializer that takes an additional 'fields' argument that
    controls which fields shoud be displayed.
    """

    def __init__(self, *args, **kwargs):
        # Don't pass the 'fields' arg up to the superclass
        fields = kwargs.pop('fields', None)

        # Instantiate the superclass normally
        super().__init__(*args, **kwargs)

        if fields is not None:
            # Drop any fields that are not specified in the 'fields' argument
            allowed = set(fields)
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)
'''

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User  # Assuming you're using Django's built-in User model
        fields = ('username', 'email', 'password', 'password2')

    # Validate that the passwords match
    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError(
                {"password": "Password fields didn't match."})
        return attrs

    # Create the user
    def create(self, validated_data):
        user = User.objects.create(
            username=validated_data['username'],
            email=validated_data['email']
        )
        # Set the user's password securely
        user.set_password(validated_data['password'])
        user.save()
        return user
    

class GuestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Guest
        fields = ['guest_id', 'first_name', 'last_name', 'email']
        read_only_fields = ['guest_id']

    
class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('email', 'username', 'password', 'password2')

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError("Passwords do not match")
        return data

    def create(self, validated_data):
        # Remove password2 before creating the user
        validated_data.pop('password2')
        user = User(
            email=validated_data['email'],
            username=validated_data['username'],
        )
        user.set_password(validated_data['password'])  # Hash the password
        user.save()
        return user
    
class OpportunityDisplaySerializer(serializers.Serializer):
    name = serializers.CharField()
    customer_segment = serializers.CharField()
    label = serializers.CharField()
    participants = serializers.IntegerField()
    scoreP = serializers.FloatField()
    scoreC = serializers.FloatField()

class EmailDisplaySerializer(serializers.Serializer):
    email = serializers.CharField()

class WorkspaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Workspace
        fields = ['workspace_id', 'name', 'user', 'code']

class OpportunitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Opportunity
        fields = ['opportunity_id', 'name', 'customer_segment', 'description', 'image', 'status', 'workspace', 'user']

class VoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vote
        fields = '__all__'
        
class IDSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    
class OpportunityResultsSerializer(serializers.Serializer):
    name = serializers.CharField()
    customer_segment = serializers.CharField()
    description = serializers.CharField()
    cur_votes = serializers.ListField(
        child = serializers.ListField(
            child = serializers.IntegerField()
        )
    )
    reasons = serializers.ListField(
        child = serializers.CharField()
    )
    imgurl = serializers.CharField()

class OpportunityVotingSerializer(serializers.Serializer):
    name = serializers.CharField()
    customer_segment = serializers.CharField()
    description = serializers.CharField()
    opportunity_id = serializers.IntegerField()
    reasons = serializers.ListField(
        child = serializers.CharField()
    )
    imgurl = serializers.CharField()
    

class VoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vote
        fields = ['vote_id', 'opportunity', 'user', 'guest',
                  'vote_score', 'criteria_id', 'user_vote_explanation']


class SessionParticipantSerializer(serializers.ModelSerializer):
    class Meta:
        model = SessionParticipant
        fields = ['participant_id', 'voting_session', 'user', 'guest']

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Guest, VotingSession, SessionParticipant
from .serializers import GuestSerializer

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
            # Find the voting session by session pin
            voting_session = VotingSession.objects.get(code=session_pin)
        except VotingSession.DoesNotExist:
            return Response({"error": "Invalid session pin"}, status=status.HTTP_404_NOT_FOUND)

        # Create or retrieve the guest
        guest, created = Guest.objects.get_or_create(
            email=email,
            defaults={
                "first_name": first_name,
                "last_name": last_name,
            }
        )

        # Associate guest with the voting session
        SessionParticipant.objects.get_or_create(
            voting_session=voting_session,
            guest=guest
        )

        return Response({"guest_id": guest.guest_id}, status=status.HTTP_201_CREATED)

        from rest_framework import serializers


class GuestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Guest
        fields = ['guest_id', 'first_name', 'last_name', 'email']
