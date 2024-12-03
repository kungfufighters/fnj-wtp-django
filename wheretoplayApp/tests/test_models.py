import pytest
from ..models import *
from django.contrib.auth import get_user_model

User = get_user_model()

""" Guest Model """
@pytest.fixture
def guest_data():
    return{
        "first_name":"John",
        "last_name":"Doe",
        "email":"john@doe.com",
    }
@pytest.fixture
def guest(guest_data):
    return Guest.objects.create(**guest_data)

@pytest.mark.django_db
def test_guest_creation(guest):
    assert guest.first_name == "John"
    assert guest.last_name == "Doe"
    assert guest.email == "john@doe.com"
    assert guest.created_at is not None

""" Workspace Model """
@pytest.fixture
def user():
    return User.objects.create_user(username="testuser", password="testpassword")

@pytest.fixture
def workspace(user):
    return Workspace.objects.create(name="Test Workspace", user=user)

@pytest.mark.django_db
def test_workspace_creation(workspace):
    assert workspace.workspace_id is not None
    assert workspace.name == "Test Workspace"
    assert workspace.user.username == "testuser"
    assert workspace.outlier_threshold == 2

@pytest.mark.django_db
def test_generate_unique_code(user):
    workspace1 = Workspace.objects.create(name="Workspace 1", user=user)
    workspace2 = Workspace.objects.create(name="Workspace 2", user=user)

    assert workspace1.code != workspace2.code  # Unique codes
    assert len(workspace1.code) == 6
    assert len(workspace2.code) == 6

@pytest.mark.django_db
def test_save_method_generates_code_and_url(workspace):
    assert workspace.code is not None  # Code is auto-generated
    assert workspace.url_link == f"http://localhost:3000/voting/{workspace.code}"  # URL is correct

@pytest.mark.django_db
def test_outlier_threshold_default(workspace):
    assert workspace.outlier_threshold == 2


@pytest.mark.django_db
def test_unique_code_across_multiple_instances(user):
    codes = set()
    for i in range(10):
        workspace = Workspace.objects.create(name=f"Workspace {i + 1}", user=user)
        codes.add(workspace.code)

    assert len(codes) == 10  # All codes should be unique