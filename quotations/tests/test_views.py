from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse

class QuotationCreateViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.client = Client()
        self.client.login(username='testuser', password='password123')
        self.url = reverse('quotation_create')

    def test_initial_point_of_contact(self):
        """Test that the point_of_contact field is autofilled with the logged-in user's username"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        
        # Check if the form in the context has the correct initial value
        form = response.context['quotation_form']
        self.assertEqual(form.initial['point_of_contact'], 'testuser')
