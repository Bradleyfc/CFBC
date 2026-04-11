"""
Basic tests for historial app models.
"""

from django.test import TestCase
from django.contrib.auth.models import User
from historial.models import (
    HistoricalArea,
    HistoricalCourseCategory,
    HistoricalCourseInformation,
    HistoricalCourseInformationAdminTeachers,
    HistoricalEnrollmentApplication,
    HistoricalEnrollmentPay,
    HistoricalAccountNumber,
    HistoricalEnrollment,
    HistoricalSubjectInformation,
    HistoricalEdition,
    HistoricalApplication,
)


class HistoricalModelsExistenceTest(TestCase):
    """Test that all 11 historical models exist and can be imported."""
    
    def test_all_models_can_be_imported(self):
        """Verify all 11 historical models can be imported."""
        models = [
            HistoricalArea,
            HistoricalCourseCategory,
            HistoricalCourseInformation,
            HistoricalCourseInformationAdminTeachers,
            HistoricalEnrollmentApplication,
            HistoricalEnrollmentPay,
            HistoricalAccountNumber,
            HistoricalEnrollment,
            HistoricalSubjectInformation,
            HistoricalEdition,
            HistoricalApplication,
        ]
        
        self.assertEqual(len(models), 11, "Should have exactly 11 historical models")
        
        for model in models:
            self.assertIsNotNone(model, f"{model.__name__} should not be None")
            self.assertTrue(hasattr(model, '_meta'), f"{model.__name__} should have _meta attribute")


class HistoricalAreaTest(TestCase):
    """Test HistoricalArea model."""
    
    def test_can_create_historical_area(self):
        """Test that HistoricalArea can be created."""
        area = HistoricalArea.objects.create(
            nombre="Test Area",
            descripcion="Test Description",
            codigo="TEST001"
        )
        
        self.assertIsNotNone(area.id)
        self.assertEqual(area.nombre, "Test Area")
        self.assertEqual(str(area), "Test Area")


class HistoricalCourseCategoryTest(TestCase):
    """Test HistoricalCourseCategory model."""
    
    def test_can_create_historical_course_category(self):
        """Test that HistoricalCourseCategory can be created."""
        category = HistoricalCourseCategory.objects.create(
            nombre="Test Category",
            descripcion="Test Description",
            es_servicio=False,
            registro_abierto=True,
            tiene_solicitud=False,
            visible=True,
            visible_comunicado=False
        )
        
        self.assertIsNotNone(category.id)
        self.assertEqual(category.nombre, "Test Category")
        self.assertEqual(str(category), "Test Category")
    
    def test_course_category_self_reference(self):
        """Test that HistoricalCourseCategory can reference itself as parent."""
        parent = HistoricalCourseCategory.objects.create(
            nombre="Parent Category",
            es_servicio=False,
            registro_abierto=True,
            tiene_solicitud=False,
            visible=True,
            visible_comunicado=False
        )
        
        child = HistoricalCourseCategory.objects.create(
            nombre="Child Category",
            parent=parent,
            es_servicio=False,
            registro_abierto=True,
            tiene_solicitud=False,
            visible=True,
            visible_comunicado=False
        )
        
        self.assertEqual(child.parent, parent)
        self.assertIn(child, parent.subcategories.all())


class HistoricalCourseInformationTest(TestCase):
    """Test HistoricalCourseInformation model."""
    
    def test_can_create_historical_course_information(self):
        """Test that HistoricalCourseInformation can be created with foreign keys."""
        area = HistoricalArea.objects.create(nombre="Test Area")
        category = HistoricalCourseCategory.objects.create(
            nombre="Test Category",
            es_servicio=False,
            registro_abierto=True,
            tiene_solicitud=False,
            visible=True,
            visible_comunicado=False
        )
        
        course = HistoricalCourseInformation.objects.create(
            nombre="Test Course",
            descripcion="Test Description",
            codigo="COURSE001",
            area=area,
            categoria=category
        )
        
        self.assertIsNotNone(course.id)
        self.assertEqual(course.nombre, "Test Course")
        self.assertEqual(course.area, area)
        self.assertEqual(course.categoria, category)
        self.assertEqual(str(course), "Test Course")


class HistoricalForeignKeyRelationshipsTest(TestCase):
    """Test foreign key relationships between historical models."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.area = HistoricalArea.objects.create(nombre="Test Area")
        self.category = HistoricalCourseCategory.objects.create(
            nombre="Test Category",
            es_servicio=False,
            registro_abierto=True,
            tiene_solicitud=False,
            visible=True,
            visible_comunicado=False
        )
        self.course = HistoricalCourseInformation.objects.create(
            nombre="Test Course",
            area=self.area,
            categoria=self.category
        )
    
    def test_enrollment_application_relationships(self):
        """Test HistoricalEnrollmentApplication foreign keys."""
        from django.utils import timezone
        
        application = HistoricalEnrollmentApplication.objects.create(
            fecha_solicitud=timezone.now(),
            estado="pending",
            curso=self.course,
            usuario=self.user
        )
        
        self.assertEqual(application.curso, self.course)
        self.assertEqual(application.usuario, self.user)
    
    def test_account_number_user_relationship(self):
        """Test HistoricalAccountNumber foreign key to User."""
        account = HistoricalAccountNumber.objects.create(
            numero_cuenta="1234567890",
            banco="Test Bank",
            usuario=self.user
        )
        
        self.assertEqual(account.usuario, self.user)
    
    def test_enrollment_pay_relationships(self):
        """Test HistoricalEnrollmentPay foreign keys."""
        from django.utils import timezone
        from decimal import Decimal
        
        application = HistoricalEnrollmentApplication.objects.create(
            fecha_solicitud=timezone.now(),
            curso=self.course,
            usuario=self.user
        )
        
        account = HistoricalAccountNumber.objects.create(
            numero_cuenta="1234567890",
            usuario=self.user
        )
        
        payment = HistoricalEnrollmentPay.objects.create(
            monto=Decimal('100.00'),
            fecha_pago=timezone.now(),
            solicitud=application,
            aceptado=True,
            cuenta=account
        )
        
        self.assertEqual(payment.solicitud, application)
        self.assertEqual(payment.cuenta, account)
    
    def test_subject_information_relationship(self):
        """Test HistoricalSubjectInformation foreign key."""
        subject = HistoricalSubjectInformation.objects.create(
            nombre="Test Subject",
            curso=self.course
        )
        
        self.assertEqual(subject.curso, self.course)
    
    def test_edition_relationships(self):
        """Test HistoricalEdition foreign keys."""
        from django.utils import timezone
        
        edition = HistoricalEdition.objects.create(
            nombre="Test Edition",
            fecha_inicio=timezone.now().date(),
            curso=self.course,
            instructor=self.user
        )
        
        self.assertEqual(edition.curso, self.course)
        self.assertEqual(edition.instructor, self.user)
    
    def test_enrollment_relationships(self):
        """Test HistoricalEnrollment foreign keys."""
        from django.utils import timezone
        
        subject = HistoricalSubjectInformation.objects.create(
            nombre="Test Subject",
            curso=self.course
        )
        
        edition = HistoricalEdition.objects.create(
            nombre="Test Edition",
            curso=self.course
        )
        
        enrollment = HistoricalEnrollment.objects.create(
            fecha_inscripcion=timezone.now(),
            curso=subject,
            usuario=self.user,
            edicion=edition,
            ausencias=0,
            intento=1
        )
        
        self.assertEqual(enrollment.curso, subject)
        self.assertEqual(enrollment.usuario, self.user)
        self.assertEqual(enrollment.edicion, edition)
    
    def test_application_relationships(self):
        """Test HistoricalApplication foreign keys."""
        from django.utils import timezone
        
        edition = HistoricalEdition.objects.create(
            nombre="Test Edition",
            curso=self.course
        )
        
        application = HistoricalApplication.objects.create(
            fecha_solicitud=timezone.now().date(),
            beca=0,
            pagado=0,
            nota_primaria=0,
            nota_secundaria=0,
            nota_final=0,
            nota_extra=0,
            curso=self.course,
            edicion=edition,
            usuario=self.user
        )
        
        self.assertEqual(application.curso, self.course)
        self.assertEqual(application.edicion, edition)
        self.assertEqual(application.usuario, self.user)


class HistoricalModelMetaTest(TestCase):
    """Test Meta configuration of historical models."""
    
    def test_all_models_have_correct_db_table_names(self):
        """Test that all models have correct database table names."""
        expected_tables = {
            HistoricalArea: 'historial_docenciaarea',
            HistoricalCourseCategory: 'historial_docenciacoursecategory',
            HistoricalCourseInformation: 'historial_docenciacourseinformation',
            HistoricalCourseInformationAdminTeachers: 'Docencia_courseinformation_adminteachers',
            HistoricalEnrollmentApplication: 'historial_docenciaenrollmentapplication',
            HistoricalEnrollmentPay: 'historial_docenciaenrollmentpay',
            HistoricalAccountNumber: 'historial_docenciaaccountnumber',
            HistoricalEnrollment: 'historial_docenciaenrollment',
            HistoricalSubjectInformation: 'historial_docenciasubjectinformation',
            HistoricalEdition: 'historial_docenciaedition',
            HistoricalApplication: 'historial_docenciaapplication',
        }

        for model, expected_table in expected_tables.items():
            self.assertEqual(
                model._meta.db_table,
                expected_table,
                f"{model.__name__} should have db_table={expected_table}"
            )

    
    def test_all_models_have_verbose_names(self):
        """Test that all models have verbose names configured."""
        models = [
            HistoricalArea,
            HistoricalCourseCategory,
            HistoricalCourseInformation,
            HistoricalCourseInformationAdminTeachers,
            HistoricalEnrollmentApplication,
            HistoricalEnrollmentPay,
            HistoricalAccountNumber,
            HistoricalEnrollment,
            HistoricalSubjectInformation,
            HistoricalEdition,
            HistoricalApplication,
        ]
        
        for model in models:
            self.assertIsNotNone(
                model._meta.verbose_name,
                f"{model.__name__} should have verbose_name"
            )
            self.assertIsNotNone(
                model._meta.verbose_name_plural,
                f"{model.__name__} should have verbose_name_plural"
            )
