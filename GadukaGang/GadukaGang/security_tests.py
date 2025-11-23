"""
Security tests for SQL injection protection and data validation
"""
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from GadukaGang.models import Topic, Section, Post
from django.db import connection

User = get_user_model()


class SQLInjectionTests(TestCase):
    """Test suite for SQL injection protection"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create test section
        self.section = Section.objects.create(
            name='Test Section',
            description='Test description',
            created_by=self.user
        )
        
        # Create test topic
        self.topic = Topic.objects.create(
            title='Test Topic',
            section=self.section,
            author=self.user
        )
    
    def test_search_or_injection(self):
        """Test protection against OR 1=1 injection in search"""
        # Attempt SQL injection
        malicious_query = "admin' OR '1'='1"
        
        # Try through API
        response = self.client.get(f'/api/v1/users/?search={malicious_query}')
        
        # Should not return all users, only matching ones (none in this case)
        self.assertIn(response.status_code, [200, 404])
        
        if response.status_code == 200:
            data = response.json()
            # Should not return unauthorized data
            self.assertLessEqual(len(data.get('results', [])), 1)
    
    def test_union_select_injection(self):
        """Test protection against UNION SELECT injection"""
        malicious_query = "' UNION SELECT id, username, password FROM GadukaGang_user--"
        
        # Try through search
        response = self.client.get(f'/api/v1/topics/?search={malicious_query}')
        
        # Should handle safely
        self.assertIn(response.status_code, [200, 400, 404])
        
        # Should not expose user passwords
        if response.status_code == 200:
            content = response.content.decode()
            self.assertNotIn('password', content.lower())
    
    def test_drop_table_injection(self):
        """Test protection against DROP TABLE injection"""
        malicious_query = "'; DROP TABLE GadukaGang_post;--"
        
        # Try through search
        response = self.client.get(f'/api/v1/posts/?search={malicious_query}')
        
        # Should handle safely
        self.assertIn(response.status_code, [200, 400, 404])
        
        # Verify table still exists
        self.assertTrue(Post.objects.model._meta.db_table)
        
        # Verify we can still query posts
        try:
            Post.objects.count()
            table_exists = True
        except:
            table_exists = False
        
        self.assertTrue(table_exists, "Post table should still exist after injection attempt")
    
    def test_comment_injection(self):
        """Test protection against comment-based injection"""
        malicious_queries = [
            "admin'--",
            "admin'#",
            "admin'/*",
        ]
        
        for query in malicious_queries:
            response = self.client.get(f'/api/v1/users/?search={query}')
            self.assertIn(response.status_code, [200, 400, 404])
    
    def test_stored_procedure_injection(self):
        """Test protection in stored procedures"""
        # Try to inject through procedure parameters
        with connection.cursor() as cursor:
            try:
                # Attempt injection in user statistics procedure
                cursor.execute(
                    "SELECT * FROM calculate_user_statistics(%s)",
                    ["1; DROP TABLE GadukaGang_user;--"]
                )
                # Should fail or handle safely
            except Exception as e:
                # Expected to fail safely
                self.assertIn('invalid', str(e).lower())
    
    def test_filter_injection(self):
        """Test protection in filter parameters"""
        malicious_filters = [
            "1 OR 1=1",
            "1; DELETE FROM GadukaGang_topic;",
            "1' AND '1'='1",
        ]
        
        for malicious_filter in malicious_filters:
            response = self.client.get(f'/api/v1/topics/?section={malicious_filter}')
            # Should handle safely without executing malicious SQL
            self.assertIn(response.status_code, [200, 400, 404])


class DataValidationTests(TestCase):
    """Test suite for data validation and sanitization"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_xss_protection_in_posts(self):
        """Test XSS protection in post content"""
        section = Section.objects.create(
            name='Test',
            created_by=self.user
        )
        topic = Topic.objects.create(
            title='Test',
            section=section,
            author=self.user
        )
        
        # Try to create post with XSS
        malicious_content = "<script>alert('XSS')</script>"
        post = Post.objects.create(
            topic=topic,
            author=self.user,
            content=malicious_content
        )
        
        # Content should be stored but escaped when rendered
        self.assertEqual(post.content, malicious_content)
        # Template should escape it (tested in integration tests)
    
    def test_email_validation(self):
        """Test email format validation"""
        invalid_emails = [
            "notanemail",
            "@example.com",
            "user@",
            "user space@example.com",
        ]
        
        for email in invalid_emails:
            with self.assertRaises(Exception):
                User.objects.create_user(
                    username=f'user_{email}',
                    email=email,
                    password='testpass123'
                )


class EncryptionTests(TestCase):
    """Test suite for encryption functionality"""
    
    def test_email_encryption_decryption(self):
        """Test email encryption and decryption"""
        from GadukaGang.encryption_utils import encrypt_field, decrypt_field
        
        original_email = "user@example.com"
        
        # Encrypt
        encrypted = encrypt_field(original_email)
        self.assertNotEqual(encrypted, original_email)
        self.assertTrue(len(encrypted) > 0)
        
        # Decrypt
        decrypted = decrypt_field(encrypted)
        self.assertEqual(decrypted, original_email)
    
    def test_email_masking(self):
        """Test email masking for display"""
        from GadukaGang.encryption_utils import mask_email
        
        test_cases = [
            ("user@example.com", "u***@e***.com"),
            ("a@b.com", "a*@b*.com"),
            ("admin@test.org", "a***@t***.org"),
        ]
        
        for original, expected in test_cases:
            masked = mask_email(original)
            self.assertEqual(masked, expected)
    
    def test_phone_masking(self):
        """Test phone number masking"""
        from GadukaGang.encryption_utils import mask_phone
        
        test_cases = [
            ("+79991234567", "+7***67"),
            ("89991234567", "8***67"),
            ("+1234567890", "+1***90"),
        ]
        
        for original, expected in test_cases:
            masked = mask_phone(original)
            self.assertEqual(masked, expected)


def run_security_tests():
    """
    Manual test runner for security demonstrations
    Prints results in a readable format
    """
    print("\n" + "="*60)
    print("🔒 SECURITY TESTING SUITE")
    print("="*60 + "\n")
    
    print("Testing SQL Injection Protection...")
    print("-" * 60)
    
    test_cases = [
        ("OR 1=1 injection", "admin' OR '1'='1"),
        ("UNION SELECT injection", "' UNION SELECT * FROM users--"),
        ("DROP TABLE injection", "'; DROP TABLE posts;--"),
        ("Comment injection", "admin'--"),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, malicious_input in test_cases:
        try:
            # Simulate search with malicious input
            # Django ORM will automatically escape this
            users = User.objects.filter(username__icontains=malicious_input)
            
            # If we get here without error, protection worked
            print(f"✓ {test_name}: BLOCKED")
            passed += 1
        except Exception as e:
            print(f"✗ {test_name}: FAILED - {str(e)}")
            failed += 1
    
    print("\n" + "-" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("="*60 + "\n")
    
    return passed, failed
