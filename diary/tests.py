from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from diary.models import Profile, Quote, DiaryEntry, Event, SharePermission, Task
import datetime
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


class SharingTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username='owner', email='owner@example.com', password='password')
        self.recipient = User.objects.create_user(username='recipient', email='recipient@example.com', password='password')
        
        self.client_owner = Client()
        self.client_owner.login(username='owner', password='password')
        
        self.client_recipient = Client()
        self.client_recipient.login(username='recipient', password='password')
        
        Quote.objects.create(text="Test quote", author="Author")
        
        # Create a diary entry
        self.entry = DiaryEntry.objects.create(user=self.owner, content="Owner's secret journal", mood="happy")
        # Create an event
        self.event = Event.objects.create(user=self.owner, title="Owner's meeting", date=datetime.date.today(), event_time="10:00")

    def test_share_diary_entry(self):
        # Owner shares a diary entry with recipient
        url = reverse('share_item')
        payload = {
            'email': 'recipient@example.com',
            'share_type': 'specific_diary',
            'item_id': self.entry.id
        }
        response = self.client_owner.post(url, data=payload, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'ok')
        
        # Verify that permission exists in database
        share = SharePermission.objects.get(owner=self.owner, shared_with_email='recipient@example.com', share_type='specific_diary')
        self.assertEqual(share.diary_entry, self.entry)
        self.assertEqual(share.shared_with_user, self.recipient)

    def test_share_whole_diary_pending_recipient(self):
        # Owner shares whole diary with a non-existing email (pending recipient)
        url = reverse('share_item')
        payload = {
            'email': 'pending@example.com',
            'share_type': 'whole_diary'
        }
        response = self.client_owner.post(url, data=payload, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'ok')
        
        share = SharePermission.objects.get(owner=self.owner, shared_with_email='pending@example.com', share_type='whole_diary')
        self.assertIsNone(share.shared_with_user)
        
        # Now, pending recipient registers
        new_user = User.objects.create_user(username='pending_user', email='pending@example.com', password='passwordNew')
        
        # The signal should run and link the user
        share.refresh_from_db()
        self.assertEqual(share.shared_with_user, new_user)

    def test_revoke_share(self):
        # Create an existing permission
        share = SharePermission.objects.create(
            owner=self.owner,
            shared_with_email='recipient@example.com',
            shared_with_user=self.recipient,
            share_type='whole_events'
        )
        
        url = reverse('revoke_share')
        payload = {
            'share_id': share.id
        }
        response = self.client_owner.post(url, data=payload, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'ok')
        
        self.assertFalse(SharePermission.objects.filter(id=share.id).exists())

    def test_event_viewset_filtering(self):
        # Initially, self.event is only owned by self.owner. Recipient shouldn't see it on calendar.
        response = self.client_recipient.get('/api/events/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 0)
        
        # Share specific event
        SharePermission.objects.create(
            owner=self.owner,
            shared_with_email='recipient@example.com',
            shared_with_user=self.recipient,
            share_type='specific_event',
            event=self.event
        )
        
        # Now event should be visible
        response = self.client_recipient.get('/api/events/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]['title'], "Owner's meeting")

    def test_share_specific_task(self):
        # Create a task for owner
        self.task = Task.objects.create(user=self.owner, title="Owner's task")
        
        # Owner shares the specific task with recipient
        url = reverse('share_item')
        payload = {
            'email': 'recipient@example.com',
            'share_type': 'specific_task',
            'item_id': self.task.id
        }
        response = self.client_owner.post(url, data=payload, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'ok')
        
        # Verify that permission exists in database
        share = SharePermission.objects.get(owner=self.owner, shared_with_email='recipient@example.com', share_type='specific_task')
        self.assertEqual(share.task, self.task)
        self.assertEqual(share.shared_with_user, self.recipient)
        
        # Verify recipient can view the shared task in task_list view
        url_tasks = reverse('task_list')
        response = self.client_recipient.get(url_tasks)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Owner's task")
        
        # Verify owner has another task that recipient cannot see
        other_task = Task.objects.create(user=self.owner, title="Owner's private task")
        response = self.client_recipient.get(url_tasks)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Owner's private task")

    def test_dashboard_upcoming_events_rendering(self):
        # Create an event that is clearly in the future so it appears in the dashboard's upcoming events
        future_date = datetime.date.today() + datetime.timedelta(days=7)
        Event.objects.create(
            user=self.owner,
            title="Future Board Meeting",
            date=future_date,
            event_time="23:00"
        )
        response = self.client_owner.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
        # Verify the template tag literal is NOT leaked in the rendered HTML
        self.assertNotContains(response, '{{ upcoming_events.0.date|date')
        # Verify the event title appears on the dashboard
        self.assertContains(response, "Future Board Meeting")
