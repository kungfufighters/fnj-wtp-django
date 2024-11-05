from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.utils import timezone
import random
import os
import qrcode

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
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    # Owner and Participant already created in table, map with pk
    category_label = models.CharField(max_length=20)

    class Meta:
        managed = True
        db_table = 'user_category'




class Workspace(models.Model):
    """Owners have their own workspace, and can have multiple"""
    workspace_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.CASCADE,null=True)
    code = models.CharField(max_length=100, null=True, blank=True)
    url_link = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        managed = True
        db_table = 'workspace'

class VotesFor(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE)

    class Meta:
        managed = True
        db_table = 'votes_for'


# Deemed unnecessary at FNJ meeting #5
'''
class OpportunityCategory(models.Model):
    opp_category_id = models.AutoField(primary_key=True)
    # Product or Service already created in table, map with pk
    label = models.CharField(max_length=100)

    class Meta:
        managed = True
        db_table = 'opportunity_category'
'''

'''
class OpportunityStatus(models.Model):
    status_id = models.AutoField(primary_key=True)
    # Pursue now, keep open, shelve already created in table, map with pk
    label = models.CharField(max_length=100, unique=True)

    class Meta:
        managed = True
        db_table = 'opportunity_status'
'''


class Opportunity(models.Model):
    opportunity_id = models.AutoField(primary_key=True)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE,null=True, blank=True)
    # Ensure this points to User
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="opportunities",null=True, blank=True)
    # opp_category = models.ForeignKey(OpportunityCategory, on_delete=models.CASCADE,null=True, blank=True)
    status = models.CharField(max_length=100, null=True, blank=True)
    name = models.CharField(max_length=100)
    customer_segment = models.CharField(max_length=100)
    description = models.TextField()
    image = models.ImageField(upload_to='images/', null=True, blank=True)

    def __str__(self):
        return self.title  # Updated to return the title instead of self.name

    class Meta:
        managed = True
        db_table = 'opportunity'

    def save(self, *args, **kwargs):
        # Save the instance first
        super().save(*args, **kwargs)

        # Now we can safely access self.id
        if not self.votingsession_set.exists():  # Only create if it doesn't exist
            pin_code = self.generate_unique_pin()
            url_link = f"{settings.PROTOCOL}://{settings.DOMAIN}/voting/{pin_code}"

            # Create the VotingSession
            VotingSession.objects.create(
                opportunity=self,
                code=pin_code,
                url_link=url_link,
                start_time=self.created_at,
                end_time=None,  # Set to None or a specific time if needed
            )

            # Generate QR Code
            self.generate_qr_code(url_link)

    def generate_unique_pin(self):
        while True:
            pin = str(random.randint(10000, 99999))  # Generate a 5-digit PIN
            if not VotingSession.objects.filter(code=pin).exists():  # Check for uniqueness
                return pin
            
    def generate_qr_code(self, url_link):
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
            os.makedirs(directory)  # Create the directory if it doesn't exist

        img_path = os.path.join(directory, f"{self.opportunity_id}.png")  # Use opportunity_id for the filename
        img.save(img_path)
        return img_path


class VotingStatus(models.Model):
    voting_status_id = models.AutoField(primary_key=True)
    voting_status = models.BooleanField(default=False)

    class Meta:
        managed = True
        db_table = 'voting_status'


class VotingSession(models.Model):
    vs_id = models.AutoField(primary_key=True)
    opportunity = models.ForeignKey(
        Opportunity, on_delete=models.CASCADE, null=True, blank=True)
    voting_status = models.ForeignKey(
        VotingStatus, on_delete=models.CASCADE, null=True, blank=True)
    code = models.CharField(max_length=5, unique=True,
                            null=True, blank=True)  # Store 5-digit PIN
    url_link = models.URLField(
        max_length=200, null=True, blank=True)  # Store URL for QR code
    # For now let it be null
    opportunity = models.ForeignKey(Opportunity, on_delete=models.CASCADE, null=True, blank=True)
    voting_status = models.ForeignKey(VotingStatus, on_delete=models.CASCADE, null=True, blank=True) 
    '''
    MOVE INTO WORKSPACE
    code = models.CharField(max_length=100, null=True, blank=True)
    url_link = models.CharField(max_length=100, null=True, blank=True)
    '''
    # Until here
    start_time = models.DateTimeField(null=True)
    end_time = models.DateTimeField(null=True)

    class Meta:
        managed = True
        db_table = 'voting_session'


class SessionParticipant(models.Model):
    """ This one would have to be in Vote """
    participant_id = models.AutoField(primary_key=True)
    voting_session = models.ForeignKey(VotingSession, on_delete=models.CASCADE)
    # Ensure this points to User
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    guest = models.ForeignKey(Guest, on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        managed = True
        db_table = 'session_participant'


class VoteCriteria(models.Model):
    criteria_id = models.AutoField(primary_key=True)
    # Reason to buy, Market Volume, etc.
    criteria_label = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    min_score = models.IntegerField(default=1)
    max_score = models.IntegerField()

    class Meta:
        managed = True
        db_table = 'vote_criteria'


class Vote (models.Model):
    vote_id = models.AutoField(primary_key=True)
    voting_session = models.ForeignKey(VotingSession, on_delete=models.CASCADE)
    criteria = models.ForeignKey(VoteCriteria, on_delete=models.CASCADE)
    # Ensure this points to User
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    guest = models.ForeignKey(Guest, on_delete=models.CASCADE, null=True, blank=True)
    # If outlier, prompt explanation
    vote_score = models.IntegerField(default=0)
    user_vote_explanation = models.TextField(null=True, blank=True)

    class Meta:
        managed = True
        db_table = 'vote'

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