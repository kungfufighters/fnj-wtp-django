from django.db import models
from django.contrib.auth.models import AbstractBaseUser

class WTPSession(models.Model):
    wtp_id = models.AutoField(primary_key=True)
    session_code = models.CharField(max_length=100)

class User(AbstractBaseUser):
    user_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)
    registration_date = models.DateField(auto_now_add=True)
    phone_number = models.CharField(max_length=100, null=True, blank=True)
    birth_date = models.DateField(null=True, blank=True)

class UserCategory(models.Model):
    user_category_id = models.IntegerField(primary_key=True)
    user_id = models.ForeignKey('User', on_delete=models.CASCADE)  # Use string reference to 'User'
    isOwner = models.BooleanField(default=False)  # This is the attribute that will allow permissions.
    isParticipant = models.BooleanField(default=False)  # Can only join, vote, follows default instructions.
    isGuest = models.BooleanField(default=False)  # Will not require account, info can be deleted?
    category = models.CharField(max_length=100)  # Owner or participant. Depends on the above boolean attributes.

# Owner Perspective

class Opportunity(models.Model):
    opportunity_id = models.AutoField(primary_key=True)
    user_id = models.ForeignKey('User', on_delete=models.CASCADE)  # isOwner == True
    name = models.CharField(max_length=100)
    description = models.TextField()

class Product(models.Model):
    product_id = models.AutoField(primary_key=True)
    opportunity_id = models.ForeignKey(Opportunity, on_delete=models.CASCADE)
    product_name = models.CharField(max_length=100)
    product_description = models.TextField()
    compelling_reason_to_buy_score = models.IntegerField()
    market_volume_score = models.IntegerField()
    economic_liability_score = models.IntegerField()
    implementation_obstacles_score = models.IntegerField()
    time_to_revenue_score = models.IntegerField()
    external_risks_score = models.IntegerField()

class Service(models.Model):
    service_id = models.AutoField(primary_key=True)
    opportunity_id = models.ForeignKey(Opportunity, on_delete=models.CASCADE)
    service_name = models.CharField(max_length=100)
    service_description = models.TextField()
    compelling_reason_to_buy_score = models.IntegerField()
    market_volume_score = models.IntegerField()
    economic_liability_score = models.IntegerField()
    implementation_obstacles_score = models.IntegerField()
    time_to_revenue_score = models.IntegerField()
    external_risks_score = models.IntegerField()