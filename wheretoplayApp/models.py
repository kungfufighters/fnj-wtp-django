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
    # Owner and Participant already created in table, map with pk
    category_label = models.CharField(max_length=20)

    class Meta:
        managed = True
        db_table = 'user_category'


class OpportunityCategory(models.Model):
    opp_category_id = models.AutoField(primary_key=True)
    # Product or Service already created in table, map with pk
    label = models.CharField(max_length=100)

    class Meta:
        managed = True
        db_table = 'opportunity_category'


class OpportunityStatus(models.Model):
    opp_status_id = models.AutoField(primary_key=True)
    # Pursue now, keep open, shelve already created in table, map with pk
    label = models.CharField(max_length=100)

    class Meta:
        managed = True
        db_table = 'opportunity_status'


class Opportunity(models.Model):
    opportunity_id = models.AutoField(primary_key=True)
    # Ensure this points to User
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    # By default, the user is Owner. (user_category_id = 1)
    user_category_id = models.ForeignKey(
        UserCategory, on_delete=models.CASCADE)
    opp_category_id = models.ForeignKey(
        OpportunityCategory, on_delete=models.CASCADE)  # Product or Service
    # Pursue now, keep open, shelve
    opp_status_id = models.ForeignKey(
        OpportunityStatus, on_delete=models.CASCADE)
    opp_name = models.CharField(max_length=100)  # e.g. Kitty Fishing
    customer_segment = models.CharField(
        max_length=100)  # Customer Segment field
    description = models.TextField()  # Description field
    image = models.ImageField(
        upload_to='images/', null=True, blank=True)  # image is optional

    class Meta:
        managed = True
        db_table = 'opportunity'


class VotingSession(models.Model):
    vs_id = models.AutoField(primary_key=True)
    opportunity_id = models.ForeignKey(Opportunity, on_delete=models.CASCADE)
    # Ensure this points to User
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=100)
    url_link = models.CharField(max_length=100)
    start_time = models.DateTimeField(null=True)
    end_time = models.DateTimeField(null=True)

    class Meta:
        managed = True
        db_table = 'voting_session'


class SessionParticipant(models.Model):
    participant_id = models.AutoField(primary_key=True)
    vs_id = models.ForeignKey(VotingSession, on_delete=models.CASCADE)
    # Ensure this points to User
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    guest_id = models.ForeignKey(Guest, on_delete=models.CASCADE)
    # By default, all are 'Participants' (user_category_id=2)
    user_category_id = models.ForeignKey(
        UserCategory, on_delete=models.CASCADE)

    class Meta:
        managed = True
        db_table = 'session_participant'


class VoteCriteria(models.Model):
    criteria_id = models.AutoField(primary_key=True)
    # Reason to buy, Market Volume, etc.
    criteria_label = models.CharField(max_length=100)
    description = models.TextField()
    min_score = models.IntegerField(default=1)
    max_score = models.IntegerField()

    class Meta:
        managed = True
        db_table = 'vote_criteria'


class Vote (models.Model):
    vote_id = models.AutoField(primary_key=True)
    vs_id = models.ForeignKey(VotingSession, on_delete=models.CASCADE)
    items_id = models.ForeignKey(VoteCriteria, on_delete=models.CASCADE)
    # Ensure this points to User
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    guest_id = models.ForeignKey(Guest, on_delete=models.CASCADE)
    vote_score = models.IntegerField(default=0)
    user_vote_explanation = models.TextField(null=True, blank=True)

    class Meta:
        managed = True
        db_table = 'vote'