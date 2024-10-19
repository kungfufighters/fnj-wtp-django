from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email

class User(models.Model):
    user_id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=50)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.CharField(max_length=100)
    password = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

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
    category_label = models.CharField(max_length=20) # Owner and Participant already created in table, map with pk

    class Meta:
        managed = True
        db_table = 'user_category'

class OpportunityCategory(models.Model):
    opp_category_id = models.AutoField(primary_key=True)
    label = models.CharField(max_length=100) #Product or Service already created in table, map with pk

    class Meta:
        managed = True
        db_table = 'opportunity_category'

class OpportunityStatus(models.Model):
    opp_status_id = models.AutoField(primary_key=True)
    label = models.CharField(max_length=100) # Pursue now, keep open, shelve already created in table, map with pk

    class Meta:
        managed = True
        db_table = 'opportunity_status'

class Opportunity(models.Model):
    opportunity_id = models.AutoField(primary_key=True)
    user_id = models.ForeignKey(User, on_delete=models.CASCADE) # Owner
    user_category_id = models.ForeignKey(UserCategory, on_delete=models.CASCADE) #By default, the user is Owner. (user_category_id = 1)
    opp_category_id = models.ForeignKey(OpportunityCategory, on_delete=models.CASCADE) # Product or Service
    opp_status_id = models.ForeignKey(OpportunityStatus, on_delete=models.CASCADE) # Pursue now, keep open, shelve
    opp_name = models.CharField(max_length=100)  # e.g. Kitty Fishing
    customer_segment = models.CharField(max_length=100) # Customer Segment field
    description = models.TextField() # Description field
    image = models.ImageField(upload_to='images/', null=True, blank=True) # image is optional

    class Meta:
        managed = True
        db_table = 'opportunity'

class VotingSession(models.Model):
    """ Asynchronous voting session... """
    vs_id = models.AutoField(primary_key=True)
    opportunity_id = models.ForeignKey(Opportunity, on_delete=models.CASCADE) # Which opportunity is being rated in this session
    user_id = models.ForeignKey(User, on_delete=models.CASCADE) # Owner, who will see ending results.
    code = models.CharField(max_length=100) # Code Displayed or Generated
    url_link = models.CharField(max_length=100) # Link to QR Code
    start_time = models.DateTimeField(null=True)
    end_time = models.DateTimeField(null=True)

    class Meta:
        managed = True
        db_table = 'voting_session'

class SessionParticipant(models.Model):
    participant_id = models.AutoField(primary_key=True)
    vs_id = models.ForeignKey(VotingSession, on_delete=models.CASCADE) # Which session is being addressed
    user_id = models.ForeignKey(User, on_delete=models.CASCADE) # These users accepted invitation to the VotingSession(vs_id) specified above
    guest_id = models.ForeignKey(Guest, on_delete=models.CASCADE) # These guests joined with a code, provided for that vs_id.
    user_category_id = models.ForeignKey(UserCategory, on_delete=models.CASCADE) # By default, all of these users are 'Participants' (user_category_id=2)

    class Meta:
        managed = True
        db_table = 'session_participant'

class VoteCriteria(models.Model):
    """ Default Voting Criteria for now """
    criteria_id = models.AutoField(primary_key=True) # For now, only 6 IDs. Maybe can expand in the future.
    criteria_label = models.CharField(max_length=100) # Reason to buy, Market Volume, etc.
    description = models.TextField() # Icon displaying short description
    min_score = models.IntegerField(default=1) # For now score ranges from 1 to 5
    max_score = models.IntegerField() # User could set more than 5 as the max score in the future.

    class Meta:
        managed = True
        db_table = 'vote_criteria'

class Vote (models.Model):
    """ User Individual Votes for Outlier Detection """
    vote_id = models.AutoField(primary_key=True)
    vs_id = models.ForeignKey(VotingSession, on_delete=models.CASCADE)
    items_id = models.ForeignKey(VoteCriteria, on_delete=models.CASCADE)
    user_id = models.ForeignKey(User, on_delete=models.CASCADE) # Which user is voting
    guest_id = models.ForeignKey(Guest, on_delete=models.CASCADE) # Guests can also vote
    vote_score = models.IntegerField(default=0) # Selected score (1 to 5)
    user_vote_explanation = models.TextField(null=True, blank=True) # If vote_score=outlier, prompt explanation (if not outlier, can be blank or null)

    class Meta:
        managed = True
        db_table = 'vote'

'''
Might be good to implement, for results confidentiality

class UserPermissions(models.Model):
    user_permissions_id = models.AutoField(primary_key=True)
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    guest_id = models.ForeignKey(Guest, on_delete=models.CASCADE)
    opportunity_id = models.ForeignKey(Opportunity, on_delete=models.CASCADE)
'''

'''
Missing Final Results Models 
'''

'''
Seems like same as votingSession, redundant 
class Voting(models.Model):
    voting_id = models.AutoField(primary_key=True)
    opportunity_id = models.ForeignKey(Opportunity, on_delete=models.CASCADE) # Which opportunity is being currently rated
   # vote_status = models.BooleanField(default=False) # Do all users finished voting? If yes, then True. Same as session
''' 