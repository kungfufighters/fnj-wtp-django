import pytest
from ..serializers import *
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password

User = get_user_model()

@pytest.fixture
def data():
    return {
        "username": "newuser",
        "email": "new@user.com",
        "password": "Pepino1233",
        "password2": "Pepino1233",
    }
@pytest.fixture
def data_password_mismatch():
    return {
        "username": "newuser",
        "email": "new@user.com",
        "password": "SecureP@ssword123",
        "password2": "DifferentPassword123",
    }

''' RegisterSerializer '''
@pytest.mark.django_db
def test_successful_registration(data):

    serializer = RegisterSerializer(data=data)

    assert serializer.is_valid(raise_exception=True)

    user = serializer.save()
    assert User.objects.count() == 1
    assert user.username == "newuser"
    assert user.email == "new@user.com"
    assert user.check_password("Pepino1233")

@pytest.mark.django_db
def test_password_mismatch(data_password_mismatch):

    serializer = RegisterSerializer(data=data_password_mismatch)
    assert not serializer.is_valid()
    assert "password" in serializer.errors
    assert serializer.errors["password"][0] == "Password fields didn't match."

@pytest.mark.django_db
def test_duplicate_email():
    User.objects.create_user(username="terminator", email="arnold@skynet.com", password="jhonConnormustLive")

    data = {
        "username": "Rambo",
        "email": "arnold@skynet.com",
        "password": "jhonConnormustLive",
        "password2": "jhonConnormustLive",
    }
    serializer = RegisterSerializer(data=data)
    assert not serializer.is_valid()
    assert "email" in serializer.errors

''' UserSerializer '''
@pytest.mark.django_db
def test_successful_user_creation(data):
    serializer = UserSerializer(data=data)
    assert serializer.is_valid(raise_exception=True)
    user = serializer.save()
    assert User.objects.count() == 1
    assert user.email == 'new@user.com'
    assert user.username == 'newuser'
    assert user.check_password("Pepino1233")

@pytest.mark.django_db
def test_user_password_mismatch(data_password_mismatch):
    serializer = UserSerializer(data=data_password_mismatch)
    assert not serializer.is_valid()
    assert "non_field_errors" in serializer.errors
    assert serializer.errors["non_field_errors"][0] == "Passwords do not match"

@pytest.mark.django_db
def test_duplicate_username(data):
    User.objects.create_user(username="newuser", email="user@example.com", password="StrongPassword123")
    serializer = UserSerializer(data=data)
    assert not serializer.is_valid()
    assert "username" in serializer.errors