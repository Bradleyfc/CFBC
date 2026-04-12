"""
Django management command to verify historial app models.
"""

from django.core.management.base import BaseCommand
from django.apps import apps
from django.db import models


class Command(BaseCommand):
    help = 'Verify that all 11 historical models are correctly defined'

    def handle(self, *args, **options):
        self.stdout.write("=" * 80)
        self.stdout.write("VERIFICATION OF HISTORIAL APP MODELS")
        self.stdout.write("=" * 80)
        self.stdout.write("")
        
        expected_models = [
            'HistoricalArea',
            'HistoricalCourseCategory',
            'HistoricalCourseInformationAdminTeachers',
            'HistoricalCourseInformation',
            'HistoricalEnrollmentApplication',
            'HistoricalEnrollmentPay',
            'HistoricalAccountNumber',
            'HistoricalEnrollment',
            'HistoricalSubjectInformation',
            'HistoricalEdition',
            'HistoricalApplication',
        ]
        
        # Check if app is registered
        try:
            app_config = apps.get_app_config('historial')
            self.stdout.write(self.style.SUCCESS(f"✓ App 'historial' is registered"))
            self.stdout.write(f"  App label: {app_config.label}")
            self.stdout.write(f"  App name: {app_config.name}")
            self.stdout.write("")
        except LookupError:
            self.stdout.write(self.style.ERROR("✗ App 'historial' is NOT registered"))
            return
        
        # Check each model
        all_models_ok = True
        for model_name in expected_models:
            try:
                model = apps.get_model('historial', model_name)
                self.stdout.write(self.style.SUCCESS(f"✓ Model '{model_name}' exists"))
                
                # Get all fields
                fields = model._meta.get_fields()
                
                # Count different types of fields
                regular_fields = [f for f in fields if isinstance(f, models.Field) and not isinstance(f, models.ForeignKey)]
                foreign_keys = [f for f in fields if isinstance(f, models.ForeignKey)]
                
                self.stdout.write(f"  - Total fields: {len(fields)}")
                self.stdout.write(f"  - Regular fields: {len(regular_fields)}")
                self.stdout.write(f"  - Foreign keys: {len(foreign_keys)}")
                
                # Show foreign key relationships
                if foreign_keys:
                    self.stdout.write(f"  - Foreign key relationships:")
                    for fk in foreign_keys:
                        related_model = fk.related_model.__name__
                        self.stdout.write(f"    • {fk.name} -> {related_model}")
                
                # Check Meta configuration
                if hasattr(model._meta, 'db_table'):
                    self.stdout.write(f"  - Database table: {model._meta.db_table}")
                if hasattr(model._meta, 'verbose_name'):
                    self.stdout.write(f"  - Verbose name: {model._meta.verbose_name}")
                
                self.stdout.write("")
                
            except LookupError:
                self.stdout.write(self.style.ERROR(f"✗ Model '{model_name}' NOT FOUND"))
                all_models_ok = False
                self.stdout.write("")
        
        # Verify foreign key relationships
        self.stdout.write("=" * 80)
        self.stdout.write("VERIFICATION OF FOREIGN KEY RELATIONSHIPS")
        self.stdout.write("=" * 80)
        self.stdout.write("")
        
        expected_relationships = {
            'HistoricalCourseCategory': {
                'parent': 'HistoricalCourseCategory',
            },
            'HistoricalCourseInformation': {
                'area': 'HistoricalArea',
                'categoria': 'HistoricalCourseCategory',
            },
            'HistoricalCourseInformationAdminTeachers': {
                'curso': 'HistoricalCourseInformation',
                'profesor': 'User',
            },
            'HistoricalEnrollmentApplication': {
                'curso': 'HistoricalCourseInformation',
                'usuario': 'User',
            },
            'HistoricalAccountNumber': {
                'usuario': 'User',
            },
            'HistoricalEnrollmentPay': {
                'solicitud': 'HistoricalEnrollmentApplication',
                'cuenta': 'HistoricalAccountNumber',
            },
            'HistoricalSubjectInformation': {
                'curso': 'HistoricalCourseInformation',
            },
            'HistoricalEdition': {
                'curso': 'HistoricalCourseInformation',
                'instructor': 'User',
            },
            'HistoricalEnrollment': {
                'curso': 'HistoricalSubjectInformation',
                'usuario': 'User',
                'edicion': 'HistoricalEdition',
            },
            'HistoricalApplication': {
                'curso': 'HistoricalCourseInformation',
                'edicion': 'HistoricalEdition',
                'usuario': 'User',
            },
        }
        
        all_relationships_ok = True
        
        for model_name, expected_fks in expected_relationships.items():
            try:
                model = apps.get_model('historial', model_name)
                self.stdout.write(f"Checking {model_name}:")
                
                for fk_name, expected_target in expected_fks.items():
                    try:
                        field = model._meta.get_field(fk_name)
                        if isinstance(field, models.ForeignKey):
                            actual_target = field.related_model.__name__
                            if actual_target == expected_target:
                                self.stdout.write(self.style.SUCCESS(f"  ✓ {fk_name} -> {actual_target}"))
                            else:
                                self.stdout.write(self.style.ERROR(f"  ✗ {fk_name} -> {actual_target} (expected {expected_target})"))
                                all_relationships_ok = False
                        else:
                            self.stdout.write(self.style.ERROR(f"  ✗ {fk_name} is not a ForeignKey"))
                            all_relationships_ok = False
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"  ✗ {fk_name} field not found: {e}"))
                        all_relationships_ok = False
                
                self.stdout.write("")
                
            except LookupError:
                self.stdout.write(self.style.ERROR(f"✗ Model '{model_name}' not found"))
                all_relationships_ok = False
                self.stdout.write("")
        
        # Summary
        self.stdout.write("=" * 80)
        if all_models_ok and all_relationships_ok:
            self.stdout.write(self.style.SUCCESS(f"✓ SUCCESS: All {len(expected_models)} historical models are correctly defined"))
            self.stdout.write(self.style.SUCCESS("✓ SUCCESS: All foreign key relationships are correct"))
        else:
            if not all_models_ok:
                self.stdout.write(self.style.ERROR("✗ FAILURE: Some models are missing or incorrectly defined"))
            if not all_relationships_ok:
                self.stdout.write(self.style.ERROR("✗ FAILURE: Some foreign key relationships are incorrect"))
        self.stdout.write("=" * 80)
