from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import random
import string
import uuid
from cloudinary.models import CloudinaryField

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
    # Ensure a default exists
    user = models.ForeignKey(User, on_delete=models.CASCADE, default=1)
    category_label = models.CharField(max_length=20)

    class Meta:
        managed = True
        db_table = 'user_category'


class Workspace(models.Model):
    workspace_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    code = models.CharField(max_length=100, null=True, blank=True)
    url_link = models.CharField(max_length=200, null=True, blank=True)
    guest_cap = models.IntegerField(default=0)

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = self.generate_unique_code()
            self.url_link = f"http://localhost:3000/voting/{self.code}"
        super().save(*args, **kwargs)

    def generate_unique_code(self):
        while True:
            code = ''.join(random.choices(
                string.ascii_uppercase + string.digits, k=6))
            if not Workspace.objects.filter(code=code).exists():
                return code

    class Meta:
        managed = True
        db_table = 'workspace'


class Opportunity(models.Model):
    opportunity_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    workspace = models.ForeignKey(
        Workspace, on_delete=models.CASCADE, default=1)
    status = models.CharField(max_length=100, null=True, blank=True)
    name = models.CharField(max_length=100)
    customer_segment = models.CharField(max_length=100)
    description = models.TextField()
    image = CloudinaryField('Image', null=True, blank=True,
                            overwrite=True, format='jpg')

    def __str__(self):
        return self.name

    class Meta:
        managed = True
        db_table = 'opportunity'


class Vote(models.Model):
    vote_id = models.AutoField(primary_key=True)
    opportunity = models.ForeignKey(
        Opportunity, on_delete=models.CASCADE, default=1)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, null=True, blank=True)
    guest = models.ForeignKey(
        Guest, on_delete=models.CASCADE, null=True, blank=True)
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
    workspace = models.ForeignKey(
        Workspace, on_delete=models.CASCADE, default=1)
    code = models.CharField(max_length=10, unique=True)
    voting_status = models.ForeignKey(
        VotingStatus, on_delete=models.CASCADE, null=True, blank=True)
    start_time = models.DateTimeField(null=True, default=timezone.now)
    expiration_time = models.DateTimeField(null=True, blank=True)

    def is_expired(self):
        """Check if the voting session is expired."""
        return self.expiration_time and timezone.now() > self.expiration_time

    class Meta:
        managed = True
        db_table = 'voting_session'


class SessionParticipant(models.Model):
    participant_id = models.AutoField(primary_key=True)
    voting_session = models.ForeignKey(VotingSession, on_delete=models.CASCADE)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, null=True, blank=True)
    guest = models.ForeignKey(
        Guest, on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        managed = True
        db_table = 'session_participant'


class Invitation(models.Model):
    invitation_id = models.AutoField(primary_key=True)
    workspace = models.ForeignKey(
        Workspace, on_delete=models.CASCADE, default=1)
    email = models.EmailField()
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    guest = models.ForeignKey(
        Guest, null=True, blank=True, on_delete=models.SET_NULL)
    sent_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        managed = True
        db_table = 'invitation'
