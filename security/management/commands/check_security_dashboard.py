"""
Django management command to check security dashboard setup.
"""

from django.core.management.base import BaseCommand
from django.test import RequestFactory
from django.contrib.auth.models import User
from django.urls import reverse, NoReverseMatch
from django.template import Template, Context
import sys


class Command(BaseCommand):
    help = 'Check security dashboard setup and configuration'

    def add_arguments(self, parser):
        parser.add_argument(
            '--create-test-admin',
            action='store_true',
            help='Create a test admin user for testing'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('=' * 60))
        self.stdout.write(self.style.MIGRATE_HEADING('Security Dashboard Setup Check'))
        self.stdout.write(self.style.MIGRATE_HEADING('=' * 60))
        
        results = []
        
        # Test 1: URL Configuration
        results.append(self.test_urls())
        
        # Test 2: View Access
        results.append(self.test_views())
        
        # Test 3: Template Tags
        results.append(self.test_template_tags())
        
        # Test 4: Admin Integration
        results.append(self.test_admin_integration())
        
        # Test 5: Create test admin if requested
        if options['create_test_admin']:
            results.append(self.create_test_admin())
        
        # Display results
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.MIGRATE_HEADING('RESULTS:'))
        
        passed = sum(results)
        total = len(results)
        
        for i, result in enumerate(results, 1):
            status = self.style.SUCCESS('✓') if result else self.style.ERROR('✗')
            self.stdout.write(f'  Test {i}: {"PASSED" if result else "FAILED"} {status}')
        
        self.stdout.write('\n' + '=' * 60)
        
        if passed == total:
            self.stdout.write(self.style.SUCCESS(f'✅ All {total} tests passed!'))
            self.stdout.write(self.style.SUCCESS('\nDashboard is ready to use:'))
            self.stdout.write(self.style.SUCCESS('1. python manage.py runserver'))
            self.stdout.write(self.style.SUCCESS('2. Log in as admin user'))
            self.stdout.write(self.style.SUCCESS('3. Go to /admin/'))
            self.stdout.write(self.style.SUCCESS('4. Click "Seguridad" button'))
            self.stdout.write(self.style.SUCCESS('5. Access dashboard at /seguridad/dashboard/'))
        else:
            self.stdout.write(self.style.ERROR(f'❌ {passed}/{total} tests passed'))
            self.stdout.write(self.style.WARNING('\nCheck the errors above and fix configuration.'))
        
        self.stdout.write('=' * 60)
        
        return 0 if passed == total else 1

    def test_urls(self):
        """Test URL configuration."""
        self.stdout.write('\n1. Testing URL configuration...')
        
        try:
            dashboard_url = reverse('security_dashboard')
            data_url = reverse('security_dashboard_data')
            
            self.stdout.write(self.style.SUCCESS(f'  ✓ Dashboard URL: {dashboard_url}'))
            self.stdout.write(self.style.SUCCESS(f'  ✓ Data API URL: {data_url}'))
            return True
        except NoReverseMatch as e:
            self.stdout.write(self.style.ERROR(f'  ✗ URL error: {e}'))
            return False
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  ✗ Unexpected error: {e}'))
            return False

    def test_views(self):
        """Test view access."""
        self.stdout.write('\n2. Testing view access...')
        
        try:
            from security import views_dashboard
            
            factory = RequestFactory()
            user = User.objects.filter(is_staff=True).first()
            
            if not user:
                # Create temporary user for test
                user = User.objects.create_user(
                    username='test_admin_temp',
                    email='test@example.com',
                    password='testpass123',
                    is_staff=True,
                    is_superuser=True
                )
                temp_user = True
            else:
                temp_user = False
            
            # Test dashboard view
            request = factory.get('/security/dashboard/')
            request.user = user
            
            try:
                response = views_dashboard.security_dashboard(request)
                self.stdout.write(self.style.SUCCESS('  ✓ Dashboard view accessible'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ✗ Dashboard view error: {e}'))
                if temp_user:
                    user.delete()
                return False
            
            # Test data API view
            request = factory.get('/security/dashboard/data/')
            request.user = user
            
            try:
                response = views_dashboard.security_dashboard_data(request)
                self.stdout.write(self.style.SUCCESS('  ✓ Data API view accessible'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ✗ Data API view error: {e}'))
                if temp_user:
                    user.delete()
                return False
            
            if temp_user:
                user.delete()
            
            return True
            
        except ImportError as e:
            self.stdout.write(self.style.ERROR(f'  ✗ Import error: {e}'))
            return False
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  ✗ Unexpected error: {e}'))
            return False

    def test_template_tags(self):
        """Test template tags."""
        self.stdout.write('\n3. Testing template tags...')
        
        try:
            # Test loading template tags
            template = Template('{% load security_admin %}')
            template.render(Context({}))
            
            self.stdout.write(self.style.SUCCESS('  ✓ Template tags loaded'))
            return True
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  ✗ Template tag error: {e}'))
            return False

    def test_admin_integration(self):
        """Test admin integration."""
        self.stdout.write('\n4. Testing admin integration...')
        
        try:
            from django.contrib import admin
            from security import models
            
            # Check key models are registered
            key_models = [
                models.UserSecurityProfile,
                models.SecurityAuditLog,
                models.SecurityReport,
                models.WAFRule,
                models.ComplianceCheck,
            ]
            
            registered = admin.site._registry
            
            for model in key_models:
                if model in registered:
                    self.stdout.write(self.style.SUCCESS(f'  ✓ {model.__name__} registered in admin'))
                else:
                    self.stdout.write(self.style.WARNING(f'  ⚠ {model.__name__} not in admin registry'))
            
            # Check template extension
            import os
            template_path = os.path.join('templates', 'admin', 'base_site.html')
            if os.path.exists(template_path):
                self.stdout.write(self.style.SUCCESS(f'  ✓ Admin template override found: {template_path}'))
            else:
                self.stdout.write(self.style.WARNING(f'  ⚠ Admin template override not found'))
            
            return True
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  ✗ Admin integration error: {e}'))
            return False

    def create_test_admin(self):
        """Create a test admin user."""
        self.stdout.write('\n5. Creating test admin user...')
        
        try:
            # Check if test admin already exists
            if User.objects.filter(username='security_admin').exists():
                self.stdout.write(self.style.WARNING('  ⚠ Test admin already exists'))
                return True
            
            # Create test admin
            user = User.objects.create_user(
                username='security_admin',
                email='security@example.com',
                password='admin123',
                is_staff=True,
                is_superuser=True,
                first_name='Security',
                last_name='Admin'
            )
            
            self.stdout.write(self.style.SUCCESS('  ✓ Test admin created successfully'))
            self.stdout.write(self.style.SUCCESS(f'    Username: security_admin'))
            self.stdout.write(self.style.SUCCESS(f'    Password: admin123'))
            self.stdout.write(self.style.SUCCESS(f'    Email: security@example.com'))
            
            return True
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  ✗ Error creating test admin: {e}'))
            return False