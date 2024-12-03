from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from ..models import Workspace

User = get_user_model()

class OpportunityCreateViewTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        self.workspace = Workspace.objects.create(
            name='Test Workspace', user=self.user
        )
        self.url = reverse('create_opportunity')


    def test_create_opportunity_success(self):
        data = {
            'workspace': self.workspace.workspace_id,
            'name': 'New Opportunity',
            'customer_segment': 'Suburbanites',
            'description':'Description of the opportunity',
        }
        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        opportunity = response.data['opportunity']
        self.assertEqual(opportunity['name'], 'New Opportunity')
        self.assertEqual(opportunity['customer_segment'], 'Suburbanites')
        self.assertEqual(opportunity['workspace'], self.workspace.workspace_id)


    def test_create_opportunity_unauthorized(self):

        self.client.logout()
        data = {
            'name': 'New Opportunity',
            'customer_segment': 'Suburbanites',
            'description': 'Description of the opportunity',
            'workspace':self.workspace.workspace_id,
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)