"""
Unit tests for Gaduka Gang Forum
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from .models import (
    Section, Topic, Post, Tag, UserRank, UserRankProgress,
    Course, CourseFavorite, Certificate, UserCertificate
)
from .forms import CustomUserCreationForm, SectionForm, PostForm
from .encryption_utils import EncryptionManager, mask_email, mask_phone
from .db_procedures import DatabaseProcedures
from .signals import check_topic_achievements

User = get_user_model()


class UserModelTest(TestCase):
    """Tests for User model and related functionality"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            role='user'
        )

    def test_user_creation(self):
        """Test that user is created correctly"""
        self.assertEqual(self.user.username, 'testuser')
        self.assertEqual(self.user.email, 'test@example.com')
        self.assertEqual(self.user.role, 'user')
        self.assertTrue(self.user.is_active)
        self.assertFalse(self.user.is_staff)
        self.assertFalse(self.user.is_superuser)

    def test_user_role_choices(self):
        """Test that user role choices are valid"""
        valid_roles = ['user', 'moderator', 'admin_level_1', 'admin_level_2', 'admin_level_3', 'super_admin']
        self.assertIn(self.user.role, valid_roles)

    def test_user_string_representation(self):
        """Test user string representation"""
        self.assertEqual(str(self.user), 'testuser')


class SectionModelTest(TestCase):
    """Tests for Section model"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.section = Section.objects.create(
            name='Test Section',
            description='Test section description',
            created_by=self.user
        )

    def test_section_creation(self):
        """Test that section is created correctly"""
        self.assertEqual(self.section.name, 'Test Section')
        self.assertEqual(self.section.description, 'Test section description')
        self.assertEqual(self.section.created_by, self.user)

    def test_section_string_representation(self):
        """Test section string representation"""
        self.assertEqual(str(self.section), 'Test Section')


class EncryptionUtilsTest(TestCase):
    """Tests for encryption utilities"""

    def setUp(self):
        """Set up test data"""
        self.encryption_manager = EncryptionManager()
        self.test_text = "This is a secret message"
        self.test_email = "test@example.com"
        self.test_phone = "+79991234567"

    def test_encryption_decryption(self):
        """Test that text can be encrypted and decrypted correctly"""
        encrypted = self.encryption_manager.encrypt(self.test_text)
        decrypted = self.encryption_manager.decrypt(encrypted)
        self.assertEqual(decrypted, self.test_text)

    def test_email_masking(self):
        """Test email masking functionality"""
        masked = mask_email(self.test_email)
        self.assertEqual(masked, "t***@e***.com")

    def test_phone_masking(self):
        """Test phone masking functionality"""
        masked = mask_phone(self.test_phone)
        self.assertEqual(masked, "+7***67")


class FormValidationTest(TestCase):
    """Tests for form validation"""

    def test_custom_user_creation_form_valid(self):
        """Test that valid user creation form is valid"""
        form_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'complexpassword123',
            'password2': 'complexpassword123',
            'privacy_policy_accepted': True
        }
        form = CustomUserCreationForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_custom_user_creation_form_invalid(self):
        """Test that invalid user creation form is not valid"""
        form_data = {
            'username': 'newuser',
            'email': 'invalid-email',
            'password1': 'pass',
            'password2': 'differentpass',
            'privacy_policy_accepted': False
        }
        form = CustomUserCreationForm(data=form_data)
        self.assertFalse(form.is_valid())
        # Check that we have validation errors (exact count may vary)
        self.assertGreater(len(form.errors), 0)


class SignalTest(TestCase):
    """Tests for Django signals"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_check_topic_achievements(self):
        """Test that check_topic_achievements function runs without error"""
        # This test ensures the function doesn't crash
        try:
            check_topic_achievements(self.user)
            success = True
        except Exception:
            success = False
        self.assertTrue(success)


class CertificateVerificationTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='certuser', email='cert@example.com', password='pass12345')
        self.certificate = Certificate.objects.create(
            name='Course Certificate',
            description='Done',
            criteria={'course_id': 1},
        )

    def test_verification_code_generated(self):
        user_cert = UserCertificate.objects.create(user=self.user, certificate=self.certificate)
        self.assertTrue(user_cert.verification_code)

    def test_verify_view_valid_and_invalid(self):
        user_cert = UserCertificate.objects.create(user=self.user, certificate=self.certificate)
        valid_resp = self.client.get(f'/certificates/verify/{user_cert.verification_code}/')
        self.assertEqual(valid_resp.status_code, 200)
        self.assertContains(valid_resp, 'Сертификат действителен')

        invalid_resp = self.client.get('/certificates/verify/not-found-code/')
        self.assertEqual(invalid_resp.status_code, 200)
        self.assertContains(invalid_resp, 'Сертификат не найден')


class FavoriteCoursesTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='favuser', email='fav@example.com', password='pass12345')
        self.visible_course = Course.objects.create(
            title='Visible',
            description='desc',
            price=0,
            is_active=True,
            status='approved',
        )
        self.hidden_course = Course.objects.create(
            title='Hidden',
            description='desc',
            price=0,
            is_active=False,
            status='approved',
        )

    def test_toggle_add_remove_favorite(self):
        self.client.login(username='favuser', password='pass12345')
        add_resp = self.client.post(f'/profile/favorites/{self.visible_course.id}/toggle/')
        self.assertEqual(add_resp.status_code, 302)
        self.assertTrue(CourseFavorite.objects.filter(user=self.user, course=self.visible_course).exists())

        remove_resp = self.client.post(f'/profile/favorites/{self.visible_course.id}/toggle/')
        self.assertEqual(remove_resp.status_code, 302)
        self.assertFalse(CourseFavorite.objects.filter(user=self.user, course=self.visible_course).exists())

    def test_toggle_for_hidden_course_forbidden(self):
        self.client.login(username='favuser', password='pass12345')
        resp = self.client.post(f'/profile/favorites/{self.hidden_course.id}/toggle/')
        self.assertEqual(resp.status_code, 302)
        self.assertFalse(CourseFavorite.objects.filter(user=self.user, course=self.hidden_course).exists())

    def test_favorites_page_only_current_user(self):
        another = User.objects.create_user(username='another', email='another@example.com', password='pass12345')
        CourseFavorite.objects.create(user=another, course=self.visible_course)
        self.client.login(username='favuser', password='pass12345')
        resp = self.client.get('/profile/favorites/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(list(resp.context['favorites']), [])
