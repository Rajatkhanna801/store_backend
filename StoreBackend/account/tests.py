from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Address

User = get_user_model()


class UserModelTest(TestCase):
    def setUp(self):
        self.user_data = {
            'username': 'testuser@example.com',
            'email': 'testuser@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'password': 'testpass123'
        }

    def test_create_user(self):
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(user.email, self.user_data['email'])
        self.assertEqual(user.first_name, self.user_data['first_name'])
        self.assertTrue(user.check_password(self.user_data['password']))


class AddressModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser@example.com',
            email='testuser@example.com',
            password='testpass123'
        )
        self.address_data = {
            'user': self.user,
            'label': 'Home',
            'address_line1': '123 Test St',
            'city': 'Test City',
            'state': 'Test State',
            'country': 'India',
            'pincode': '123456'
        }

    def test_create_address(self):
        address = Address.objects.create(**self.address_data)
        self.assertEqual(address.user, self.user)
        self.assertEqual(address.label, 'Home')
        self.assertEqual(address.city, 'Test City')


class AccountAPITest(APITestCase):
    def setUp(self):
        self.user_data = {
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'testuser@example.com',
            'phone_number': '+919999999999',
            'password': 'testpass123'
        }
        self.login_data = {
            'email': 'testuser@example.com',
            'password': 'testpass123'
        }

    def test_user_registration(self):
        url = '/api/accounts/register/'
        response = self.client.post(url, self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(User.objects.get().email, 'testuser@example.com')

    def test_user_login(self):
        # Create user first
        User.objects.create_user(
            username='testuser@example.com',
            email='testuser@example.com',
            password='testpass123'
        )
        
        url = '/api/accounts/login/'
        response = self.client.post(url, self.login_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access_token', response.data)
        self.assertIn('refresh_token', response.data)
        self.assertIn('user', response.data)

    def test_protected_endpoint_without_token(self):
        url = '/api/accounts/me/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_protected_endpoint_with_token(self):
        # Create user and get token
        user = User.objects.create_user(
            username='testuser@example.com',
            email='testuser@example.com',
            password='testpass123'
        )
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        
        url = '/api/accounts/me/'
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'testuser@example.com')

    def test_token_refresh(self):
        # Create user and get token
        user = User.objects.create_user(
            username='testuser@example.com',
            email='testuser@example.com',
            password='testpass123'
        )
        refresh = RefreshToken.for_user(user)
        refresh_token = str(refresh)
        
        url = '/api/accounts/token/refresh/'
        response = self.client.post(url, {'refresh': refresh_token}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_logout(self):
        # Create user and get token
        user = User.objects.create_user(
            username='testuser@example.com',
            email='testuser@example.com',
            password='testpass123'
        )
        refresh = RefreshToken.for_user(user)
        refresh_token = str(refresh)
        access_token = str(refresh.access_token)
        
        url = '/api/accounts/logout/'
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = self.client.post(url, {'refresh_token': refresh_token}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'Logged out successfully.')


class AddressAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser@example.com',
            email='testuser@example.com',
            password='testpass123'
        )
        self.refresh = RefreshToken.for_user(self.user)
        self.access_token = str(self.refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        
        self.address_data = {
            'label': 'Home',
            'address_line1': '123 Test St',
            'city': 'Test City',
            'state': 'Test State',
            'country': 'India',
            'pincode': '123456'
        }

    def test_create_address(self):
        url = '/api/accounts/addresses/'
        response = self.client.post(url, self.address_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Address.objects.count(), 1)
        self.assertEqual(Address.objects.get().user, self.user)

    def test_list_addresses(self):
        Address.objects.create(user=self.user, **self.address_data)
        url = '/api/accounts/addresses/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
