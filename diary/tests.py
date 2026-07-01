from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from diary.models import Profile, Quote
from diary.context_processors import quote_context

class QuoteTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        self.client = Client()
        self.client.login(username='testuser', password='password')
        
        # Create some default random quotes
        Quote.objects.create(text="Random Quote 1", author="Author 1")
        Quote.objects.create(text="Random Quote 2", author="Author 2")

    def test_context_processor_with_no_profile(self):
        # Even without existing Profile, Profile is created and random quote is retrieved
        self.assertFalse(Profile.objects.filter(user=self.user).exists())
        
        # Mock request object
        class MockRequest:
            user = self.user
        
        context = quote_context(MockRequest())
        self.assertIn(context['quote_text'], ["Random Quote 1", "Random Quote 2"])
        self.assertFalse(context['quote_is_custom'])
        
        # Profile should be created automatically
        self.assertTrue(Profile.objects.filter(user=self.user).exists())

    def test_save_custom_quote(self):
        save_url = reverse('save_custom_quote')
        payload = {
            'text': 'My beautiful custom quote',
            'author': 'Myself'
        }
        response = self.client.post(save_url, data=payload, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'ok')
        self.assertEqual(data['text'], 'My beautiful custom quote')
        self.assertEqual(data['author'], 'Myself')
        
        # Verify persistence in Database
        profile = Profile.objects.get(user=self.user)
        self.assertEqual(profile.custom_quote, 'My beautiful custom quote')
        self.assertEqual(profile.custom_quote_author, 'Myself')
        
        # Context processor should now return this custom quote
        class MockRequest:
            user = self.user
        
        context = quote_context(MockRequest())
        self.assertEqual(context['quote_text'], 'My beautiful custom quote')
        self.assertEqual(context['quote_author'], 'Myself')
        self.assertTrue(context['quote_is_custom'])

    def test_delete_custom_quote(self):
        # First save a custom quote
        profile, _ = Profile.objects.get_or_create(user=self.user)
        profile.custom_quote = 'Custom Quote'
        profile.custom_quote_author = 'Author'
        profile.save()
        
        delete_url = reverse('delete_custom_quote')
        response = self.client.post(delete_url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'ok')
        self.assertIn(data['text'], ["Random Quote 1", "Random Quote 2"])
        
        # Verify deletion in Database
        profile.refresh_from_db()
        self.assertEqual(profile.custom_quote, None)
        self.assertEqual(profile.custom_quote_author, None)


class PasswordChangeTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='pwuser', password='old_password123')
        self.client = Client()
        self.client.login(username='pwuser', password='old_password123')
        Quote.objects.create(text="Test Quote", author="Tester")

    def test_password_change_success(self):
        url = reverse('settings_view')
        payload = {
            'action': 'change_password',
            'old_password': 'old_password123',
            'new_password1': 'new_valid_password123',
            'new_password2': 'new_valid_password123'
        }
        response = self.client.post(url, data=payload)
        self.assertEqual(response.status_code, 302) # Should redirect on success
        
        # Verify password got changed
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('new_valid_password123'))
        
        # Verify user is still authenticated (due to update_session_auth_hash)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_password_change_wrong_old_password(self):
        url = reverse('settings_view')
        payload = {
            'action': 'change_password',
            'old_password': 'wrong_password',
            'new_password1': 'new_valid_password123',
            'new_password2': 'new_valid_password123'
        }
        response = self.client.post(url, data=payload)
        self.assertEqual(response.status_code, 200) # Should render with errors
        
        # Verify password was not changed
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('old_password123'))

    def test_password_change_mismatched_new_passwords(self):
        url = reverse('settings_view')
        payload = {
            'action': 'change_password',
            'old_password': 'old_password123',
            'new_password1': 'new_valid_password123',
            'new_password2': 'different_password123'
        }
        response = self.client.post(url, data=payload)
        self.assertEqual(response.status_code, 200) # Should render with errors
        
        # Verify password was not changed
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('old_password123'))
