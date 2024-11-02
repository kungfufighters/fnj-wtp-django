from cloudinary.models import CloudinaryField
from django.db import models
from django.contrib.auth.models import AbstractUser

# Updated User model extending AbstractUser


class User(AbstractUser):
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email


class Guest(models.Model):
    guest_id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100, null=True, blank=True)
    email = models.CharField(max_length=100)
    created_at = models.DateField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = 'guest'


class UserCategory(models.Model):
    user_category_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    # Owner and Participant already created in table, map with pk
    category_label = models.CharField(max_length=20)

    class Meta:
        managed = True
        db_table = 'user_category'


class Workspace(models.Model):
    workspace_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    code = models.CharField(max_length=100, unique=True)  # Used as the active session code
    url_link = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        managed = True
        db_table = 'workspace'


class Opportunity(models.Model):
    opportunity_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE)
    status = models.CharField(max_length=100, null=True, blank=True)
    name = models.CharField(max_length=100)
    customer_segment = models.CharField(max_length=100)
    description = models.TextField()
    image = CloudinaryField('Image', overwrite=True, format='jpg')

    def __str__(self):
        return self.name

    class Meta:
        managed = True
        db_table = 'opportunity'


class Vote(models.Model):
    vote_id = models.AutoField(primary_key=True)
    opportunity = models.ForeignKey(Opportunity, on_delete=models.CASCADE)  # Tied directly to an Opportunity
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    vote_score = models.IntegerField(default=0)
    criteria_id = models.IntegerField(null=True, blank=True) 
    user_vote_explanation = models.TextField(null=True, blank=True)

    class Meta:
        managed = True
        db_table = 'vote'


class VotingStatus(models.Model):
    voting_status_id = models.AutoField(primary_key=True)
    voting_status = models.BooleanField(default=False)

    class Meta:
        managed = True
        db_table = 'voting_status'


class VotingSession(models.Model):
    session_id = models.AutoField(primary_key=True)
    code = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='voting_sessions', null=True, blank=True)
    voting_status = models.ForeignKey(VotingStatus, on_delete=models.CASCADE, null=True, blank=True)
    start_time = models.DateTimeField(null=True)
    end_time = models.DateTimeField(null=True)

    class Meta:
        managed = True
        db_table = 'voting_session'


class SessionParticipant(models.Model):
    participant_id = models.AutoField(primary_key=True)
    voting_session = models.ForeignKey(VotingSession, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        managed = True
        db_table = 'session_participant'


'''
AbstractUser has it

class UserPermissions(models.Model):
    user_permission_id = models.AutoField(primary_key=True)
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    workspace_id = models.ForeignKey(Workspace, on_delete=models.CASCADE)

    class Meta:
        managed = True
        db_table = 'user_permissions'
'''