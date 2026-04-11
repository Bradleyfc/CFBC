"""
Verification script for historial app models.
This script verifies that all 11 historical models are correctly defined.
"""

from django.apps import apps
from django.db import models
from django.contrib.auth.models import User


def verify_all_models():
    """Verify all 11 historical models exist and are properly configured."""
    
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
    
    print("=" * 80)
    print("VERIFICATION OF HISTORIAL APP MODELS")
    print("=" * 80)
    print()
    
    # Check if app is registered
    try:
        app_config = apps.get_app_config('historial')
        print(f"✓ App 'historial' is registered")
        print(f"  App label: {app_config.label}")
        print(f"  App name: {app_config.name}")
        print()
    except LookupError:
        print("✗ App 'historial' is NOT registered in INSTALLED_APPS")
        return False
    
    # Check each model
    all_models_ok = True
    for model_name in expected_models:
        try:
            model = apps.get_model('historial', model_name)
            print(f"✓ Model '{model_name}' exists")
            
            # Get all fields
            fields = model._meta.get_fields()
            field_names = [f.name for f in fields]
            
            # Count different types of fields
            regular_fields = [f for f in fields if isinstance(f, models.Field) and not isinstance(f, models.ForeignKey)]
            foreign_keys = [f for f in fields if isinstance(f, models.ForeignKey)]
            
            print(f"  - Total fields: {len(fields)}")
            print(f"  - Regular fields: {len(regular_fields)}")
            print(f"  - Foreign keys: {len(foreign_keys)}")
            
            # Show foreign key relationships
            if foreign_keys:
                print(f"  - Foreign key relationships:")
                for fk in foreign_keys:
                    related_model = fk.related_model.__name__
                    print(f"    • {fk.name} -> {related_model}")
            
            # Check Meta configuration
            if hasattr(model._meta, 'db_table'):
                print(f"  - Database table: {model._meta.db_table}")
            if hasattr(model._meta, 'verbose_name'):
                print(f"  - Verbose name: {model._meta.verbose_name}")
            
            print()
            
        except LookupError:
            print(f"✗ Model '{model_name}' NOT FOUND")
            all_models_ok = False
            print()
    
    # Summary
    print("=" * 80)
    if all_models_ok:
        print(f"✓ SUCCESS: All {len(expected_models)} historical models are correctly defined")
    else:
        print("✗ FAILURE: Some models are missing or incorrectly defined")
    print("=" * 80)
    
    return all_models_ok


def verify_foreign_key_relationships():
    """Verify that foreign keys point to the correct models."""
    
    print()
    print("=" * 80)
    print("VERIFICATION OF FOREIGN KEY RELATIONSHIPS")
    print("=" * 80)
    print()
    
    # Expected relationships
    expected_relationships = {
        'HistoricalCourseCategory': {
            'parent': 'HistoricalCourseCategory',  # Self-reference
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
            print(f"Checking {model_name}:")
            
            for fk_name, expected_target in expected_fks.items():
                try:
                    field = model._meta.get_field(fk_name)
                    if isinstance(field, models.ForeignKey):
                        actual_target = field.related_model.__name__
                        if actual_target == expected_target:
                            print(f"  ✓ {fk_name} -> {actual_target}")
                        else:
                            print(f"  ✗ {fk_name} -> {actual_target} (expected {expected_target})")
                            all_relationships_ok = False
                    else:
                        print(f"  ✗ {fk_name} is not a ForeignKey")
                        all_relationships_ok = False
                except Exception as e:
                    print(f"  ✗ {fk_name} field not found: {e}")
                    all_relationships_ok = False
            
            print()
            
        except LookupError:
            print(f"✗ Model '{model_name}' not found")
            all_relationships_ok = False
            print()
    
    print("=" * 80)
    if all_relationships_ok:
        print("✓ SUCCESS: All foreign key relationships are correct")
    else:
        print("✗ FAILURE: Some foreign key relationships are incorrect")
    print("=" * 80)
    
    return all_relationships_ok


if __name__ == '__main__':
    import django
    import os
    
    # Setup Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cfbc.settings')
    django.setup()
    
    # Run verifications
    models_ok = verify_all_models()
    relationships_ok = verify_foreign_key_relationships()
    
    # Exit with appropriate code
    if models_ok and relationships_ok:
        print("\n✓ ALL VERIFICATIONS PASSED")
        exit(0)
    else:
        print("\n✗ SOME VERIFICATIONS FAILED")
        exit(1)
