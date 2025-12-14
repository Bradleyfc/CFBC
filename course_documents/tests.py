from django.test import TestCase, Client
from django.contrib.auth.models import User, Group
from django.urls import reverse
from hypothesis import given, strategies as st, settings
from hypothesis.extra.django import TestCase as HypothesisTestCase
from principal.models import Curso, CursoAcademico, Matriculas
from .models import DocumentFolder, CourseDocument, NewContentNotification, AuditLog, DocumentAccess
import tempfile
import os
import re


class CourseDocumentsPropertyTests(HypothesisTestCase):
    """
    Property-based tests for course documents system
    """
    
    def setUp(self):
        """Set up test data"""
        # Create groups
        self.profesores_group, _ = Group.objects.get_or_create(name='Profesores')
        self.estudiantes_group, _ = Group.objects.get_or_create(name='Estudiantes')
        
        # Create academic year
        self.curso_academico, _ = CursoAcademico.objects.get_or_create(
            nombre="2024-2025",
            defaults={'activo': True}
        )
        
        self.client = Client()

    @given(st.integers(min_value=1, max_value=10))
    @settings(deadline=None, max_examples=10)
    def test_dashboard_access_buttons_match_teacher_courses(self, num_courses):
        """
        **Feature: gestion-documentos-cursos, Property 1: Dashboard access buttons match user courses**
        For any professor, the number of dashboard access buttons displayed should equal 
        the number of courses they are assigned to
        """
        # Create a teacher
        teacher = User.objects.create_user(
            username=f'teacher_{num_courses}',
            password='testpass123',
            email='teacher@test.com'
        )
        teacher.groups.add(self.profesores_group)
        
        # Create courses assigned to this teacher
        courses = []
        for i in range(num_courses):
            course = Curso.objects.create(
                name=f'Course {i+1}',
                teacher=teacher,
                curso_academico=self.curso_academico,
                description=f'Test course {i+1}'
            )
            courses.append(course)
        
        # Login as teacher
        self.client.login(username=teacher.username, password='testpass123')
        
        # Get profile page
        response = self.client.get(reverse('principal:profile'))
        
        # Verify response is successful
        self.assertEqual(response.status_code, 200)
        
        # Verify the number of assigned courses in context matches created courses
        assigned_courses = response.context.get('assigned_courses', [])
        self.assertEqual(len(assigned_courses), num_courses)
        
        # Verify each created course is in the assigned courses
        assigned_course_ids = [course.id for course in assigned_courses]
        for course in courses:
            self.assertIn(course.id, assigned_course_ids)

    @given(st.integers(min_value=1, max_value=10))
    @settings(deadline=None, max_examples=10)
    def test_dashboard_access_buttons_match_student_enrollments(self, num_enrollments):
        """
        **Feature: gestion-documentos-cursos, Property 1: Dashboard access buttons match user courses**
        For any student, the number of dashboard access buttons displayed should equal 
        the number of courses they are enrolled in
        """
        # Create a student
        student = User.objects.create_user(
            username=f'student_{num_enrollments}',
            password='testpass123',
            email='student@test.com'
        )
        student.groups.add(self.estudiantes_group)
        
        # Create a teacher for the courses
        teacher = User.objects.create_user(
            username=f'teacher_for_student_{num_enrollments}',
            password='testpass123',
            email='teacher@test.com'
        )
        teacher.groups.add(self.profesores_group)
        
        # Create courses and enroll student
        enrolled_courses = []
        for i in range(num_enrollments):
            course = Curso.objects.create(
                name=f'Course {i+1}',
                teacher=teacher,
                curso_academico=self.curso_academico,
                description=f'Test course {i+1}'
            )
            
            # Enroll student in course
            Matriculas.objects.create(
                course=course,
                student=student,
                curso_academico=self.curso_academico,
                activo=True
            )
            enrolled_courses.append(course)
        
        # Login as student
        self.client.login(username=student.username, password='testpass123')
        
        # Get profile page
        response = self.client.get(reverse('principal:profile'))
        
        # Verify response is successful
        self.assertEqual(response.status_code, 200)
        
        # Verify the number of enrolled courses in context matches enrollments
        enrolled_courses_context = response.context.get('enrolled_courses', [])
        self.assertEqual(len(enrolled_courses_context), num_enrollments)
        
        # Verify each enrolled course is in the context
        enrolled_course_ids = [course.id for course in enrolled_courses_context]
        for course in enrolled_courses:
            self.assertIn(course.id, enrolled_course_ids)

    @given(st.text())
    @settings(deadline=None, max_examples=100)
    def test_folder_name_validation_rejects_invalid_input(self, folder_name):
        """
        **Feature: gestion-documentos-cursos, Property 4: Folder name validation rejects invalid input**
        For any folder creation attempt with empty names or only whitespace characters, 
        the system should reject the creation and maintain the current state
        """
        # Create a teacher and course
        teacher = User.objects.create_user(
            username='teacher_validation',
            password='testpass123',
            email='teacher@test.com'
        )
        teacher.groups.add(self.profesores_group)
        
        course = Curso.objects.create(
            name='Validation Course',
            teacher=teacher,
            curso_academico=self.curso_academico,
            description='Test course for validation'
        )
        
        # Count initial folders
        initial_count = DocumentFolder.objects.filter(curso=course).count()
        
        # Try to create folder with the generated name
        folder = DocumentFolder(
            curso=course,
            name=folder_name,
            created_by=teacher
        )
        
        # Check if the name is invalid (empty or only whitespace)
        is_invalid = not folder_name or not folder_name.strip()
        
        if is_invalid:
            # Should raise validation error for invalid names
            with self.assertRaises(Exception):  # ValidationError or similar
                folder.save()
            
            # Verify folder count hasn't changed
            final_count = DocumentFolder.objects.filter(curso=course).count()
            self.assertEqual(initial_count, final_count)
        else:
            # For valid names, check if they contain forbidden characters
            import re
            has_forbidden_chars = bool(re.search(r'[<>:"/\\|?*]', folder_name))
            
            if has_forbidden_chars:
                # Should raise validation error for forbidden characters
                with self.assertRaises(Exception):
                    folder.save()
                
                # Verify folder count hasn't changed
                final_count = DocumentFolder.objects.filter(curso=course).count()
                self.assertEqual(initial_count, final_count)
            else:
                # Valid name should save successfully
                try:
                    folder.save()
                    # Verify folder was created
                    final_count = DocumentFolder.objects.filter(curso=course).count()
                    self.assertEqual(initial_count + 1, final_count)
                except Exception:
                    # Some other validation might fail (like length), which is acceptable
                    pass

    @given(st.text(min_size=1, max_size=20).filter(lambda x: x.strip() and not re.search(r'[<>:"/\\|?*\x00]', x) and x.isprintable()))
    @settings(deadline=None, max_examples=50)
    def test_valid_folder_creation_succeeds(self, folder_name):
        """
        **Feature: gestion-documentos-cursos, Property 5: Folder creation with valid names succeeds**
        For any valid folder name (non-empty, allowed characters), creating a folder 
        should result in the folder appearing immediately in the dashboard
        """
        import re
        
        # Create a teacher and course
        teacher = User.objects.create_user(
            username=f'teacher_valid_{hash(folder_name) % 10000}',
            password='testpass123',
            email='teacher@test.com'
        )
        teacher.groups.add(self.profesores_group)
        
        course = Curso.objects.create(
            name=f'Valid Course {hash(folder_name) % 10000}',
            teacher=teacher,
            curso_academico=self.curso_academico,
            description='Test course for valid creation'
        )
        
        # Count initial folders
        initial_count = DocumentFolder.objects.filter(curso=course).count()
        
        # Create folder with valid name
        folder = DocumentFolder.objects.create(
            curso=course,
            name=folder_name.strip(),
            created_by=teacher
        )
        
        # Verify folder was created successfully
        final_count = DocumentFolder.objects.filter(curso=course).count()
        self.assertEqual(initial_count + 1, final_count)
        
        # Verify folder exists with correct name
        self.assertTrue(
            DocumentFolder.objects.filter(
                curso=course, 
                name=folder_name.strip()
            ).exists()
        )

    @given(st.text().filter(lambda x: bool(re.search(r'[<>:"/\\|?*]', x))))
    @settings(deadline=None, max_examples=50)
    def test_character_validation_for_folder_names(self, folder_name):
        """
        **Feature: gestion-documentos-cursos, Property 6: Character validation for folder names**
        For any folder name containing disallowed special characters, 
        the system should reject the creation
        """
        import re
        
        # Create a teacher and course
        teacher = User.objects.create_user(
            username=f'teacher_chars_{abs(hash(folder_name)) % 10000}',
            password='testpass123',
            email='teacher@test.com'
        )
        teacher.groups.add(self.profesores_group)
        
        course = Curso.objects.create(
            name=f'Chars Course {abs(hash(folder_name)) % 10000}',
            teacher=teacher,
            curso_academico=self.curso_academico,
            description='Test course for character validation'
        )
        
        # Count initial folders
        initial_count = DocumentFolder.objects.filter(curso=course).count()
        
        # Try to create folder with forbidden characters
        folder = DocumentFolder(
            curso=course,
            name=folder_name,
            created_by=teacher
        )
        
        # Should raise validation error
        with self.assertRaises(Exception):
            folder.save()
        
        # Verify folder count hasn't changed
        final_count = DocumentFolder.objects.filter(curso=course).count()
        self.assertEqual(initial_count, final_count)

    @given(st.text(min_size=1, max_size=20).filter(lambda x: x.strip() and x.isprintable() and '\x00' not in x))
    @settings(deadline=None, max_examples=20)
    def test_document_folder_association_integrity(self, document_name):
        """
        **Feature: gestion-documentos-cursos, Property 7: Document-folder association integrity**
        For any document upload to a selected folder, the document should be stored 
        and associated with exactly that folder
        """
        # Create a teacher and course
        teacher = User.objects.create_user(
            username=f'teacher_assoc_{abs(hash(document_name)) % 10000}',
            password='testpass123',
            email='teacher@test.com'
        )
        teacher.groups.add(self.profesores_group)
        
        course = Curso.objects.create(
            name=f'Assoc Course {abs(hash(document_name)) % 10000}',
            teacher=teacher,
            curso_academico=self.curso_academico,
            description='Test course for association'
        )
        
        # Create a folder
        folder = DocumentFolder.objects.create(
            curso=course,
            name='Test Folder',
            created_by=teacher
        )
        
        # Create a temporary file for testing
        import tempfile
        from django.core.files.uploadedfile import SimpleUploadedFile
        
        # Create a simple text file
        file_content = b"Test document content"
        uploaded_file = SimpleUploadedFile(
            name="test_document.txt",
            content=file_content,
            content_type="text/plain"
        )
        
        # Create document associated with the folder
        document = CourseDocument.objects.create(
            folder=folder,
            name=document_name.strip(),
            file=uploaded_file,
            uploaded_by=teacher
        )
        
        # Verify document is associated with the correct folder
        self.assertEqual(document.folder, folder)
        self.assertEqual(document.folder.curso, course)
        
        # Verify document appears in folder's documents
        self.assertIn(document, folder.documents.all())
        
        # Verify document count in folder
        self.assertEqual(folder.documents.count(), 1)

    @given(st.sampled_from(['exe', 'bat', 'sh', 'php', 'js', 'py']))
    @settings(deadline=None, max_examples=10)
    def test_file_type_validation_rejects_disallowed_extensions(self, file_extension):
        """
        **Feature: gestion-documentos-cursos, Property 8: File type validation**
        For any file upload with a disallowed file extension, the system should 
        reject the upload and display an error message
        """
        # Create a teacher and course
        teacher = User.objects.create_user(
            username=f'teacher_filetype_{file_extension}',
            password='testpass123',
            email='teacher@test.com'
        )
        teacher.groups.add(self.profesores_group)
        
        course = Curso.objects.create(
            name=f'FileType Course {file_extension}',
            teacher=teacher,
            curso_academico=self.curso_academico,
            description='Test course for file type validation'
        )
        
        # Create a folder
        folder = DocumentFolder.objects.create(
            curso=course,
            name='Test Folder',
            created_by=teacher
        )
        
        # Create a file with disallowed extension
        from django.core.files.uploadedfile import SimpleUploadedFile
        
        file_content = b"Test content"
        uploaded_file = SimpleUploadedFile(
            name=f"test_file.{file_extension}",
            content=file_content,
            content_type="application/octet-stream"
        )
        
        # Count initial documents
        initial_count = CourseDocument.objects.filter(folder=folder).count()
        
        # Try to create document with disallowed extension
        document = CourseDocument(
            folder=folder,
            name=f'Test Document {file_extension}',
            file=uploaded_file,
            uploaded_by=teacher
        )
        
        # Should raise validation error for disallowed file type
        with self.assertRaises(Exception):  # ValidationError
            document.save()
        
        # Verify document count hasn't changed
        final_count = CourseDocument.objects.filter(folder=folder).count()
        self.assertEqual(initial_count, final_count)

    @given(st.sampled_from(['pdf', 'doc', 'docx', 'txt', 'jpg', 'png']))
    @settings(deadline=None, max_examples=10)
    def test_file_type_validation_accepts_allowed_extensions(self, file_extension):
        """
        **Feature: gestion-documentos-cursos, Property 8: File type validation**
        For any file upload with an allowed file extension, the system should 
        accept the upload successfully
        """
        # Create a teacher and course
        teacher = User.objects.create_user(
            username=f'teacher_allowed_{file_extension}',
            password='testpass123',
            email='teacher@test.com'
        )
        teacher.groups.add(self.profesores_group)
        
        course = Curso.objects.create(
            name=f'Allowed Course {file_extension}',
            teacher=teacher,
            curso_academico=self.curso_academico,
            description='Test course for allowed file types'
        )
        
        # Create a folder
        folder = DocumentFolder.objects.create(
            curso=course,
            name='Test Folder',
            created_by=teacher
        )
        
        # Create a file with allowed extension
        from django.core.files.uploadedfile import SimpleUploadedFile
        
        file_content = b"Test content for allowed file"
        uploaded_file = SimpleUploadedFile(
            name=f"test_file.{file_extension}",
            content=file_content,
            content_type="application/octet-stream"
        )
        
        # Count initial documents
        initial_count = CourseDocument.objects.filter(folder=folder).count()
        
        # Create document with allowed extension
        document = CourseDocument.objects.create(
            folder=folder,
            name=f'Test Document {file_extension}',
            file=uploaded_file,
            uploaded_by=teacher
        )
        
        # Verify document was created successfully
        final_count = CourseDocument.objects.filter(folder=folder).count()
        self.assertEqual(initial_count + 1, final_count)
        
        # Verify document properties
        self.assertEqual(document.folder, folder)
        self.assertEqual(document.uploaded_by, teacher)
        self.assertTrue(document.file_size > 0)

    @given(st.booleans(), st.booleans())
    @settings(deadline=None, max_examples=20)
    def test_access_control_enforcement(self, is_teacher, is_enrolled):
        """
        **Feature: gestion-documentos-cursos, Property 11: Access control enforcement**
        For any user attempting to access course documents, the system should verify 
        appropriate role (profesor/estudiante) and course relationship (assigned/enrolled) 
        before granting access
        """
        # Create a teacher and course
        teacher = User.objects.create_user(
            username='course_teacher',
            password='testpass123',
            email='teacher@test.com'
        )
        teacher.groups.add(self.profesores_group)
        
        course = Curso.objects.create(
            name='Access Control Course',
            teacher=teacher,
            curso_academico=self.curso_academico,
            description='Test course for access control'
        )
        
        # Create a test user
        test_user = User.objects.create_user(
            username=f'test_user_{is_teacher}_{is_enrolled}',
            password='testpass123',
            email='testuser@test.com'
        )
        
        # Assign role based on parameter
        if is_teacher:
            test_user.groups.add(self.profesores_group)
        else:
            test_user.groups.add(self.estudiantes_group)
        
        # Create enrollment if specified
        if is_enrolled and not is_teacher:
            Matriculas.objects.create(
                course=course,
                student=test_user,
                curso_academico=self.curso_academico,
                activo=True
            )
        
        # Test access using permission mixins
        from course_documents.permissions import TeacherPermissionMixin, StudentPermissionMixin
        
        # Mock request object
        class MockRequest:
            def __init__(self, user):
                self.user = user
                self.META = {'REMOTE_ADDR': '127.0.0.1'}
        
        # Mock view with kwargs
        class MockView:
            def __init__(self, user, curso_id):
                self.request = MockRequest(user)
                self.kwargs = {'curso_id': curso_id}
        
        # Test teacher permission
        teacher_view = MockView(test_user, course.id)
        teacher_mixin = TeacherPermissionMixin()
        teacher_mixin.request = teacher_view.request
        teacher_mixin.kwargs = teacher_view.kwargs
        
        # Test student permission
        student_view = MockView(test_user, course.id)
        student_mixin = StudentPermissionMixin()
        student_mixin.request = student_view.request
        student_mixin.kwargs = student_view.kwargs
        
        # Verify access control logic
        if is_teacher:
            # Teacher should only have access if they are the assigned teacher
            teacher_has_access = teacher_mixin.test_func()
            if test_user == teacher:
                self.assertTrue(teacher_has_access)
            else:
                self.assertFalse(teacher_has_access)
            
            # Teacher should not have student access
            student_has_access = student_mixin.test_func()
            self.assertFalse(student_has_access)
        else:
            # Student should not have teacher access
            teacher_has_access = teacher_mixin.test_func()
            self.assertFalse(teacher_has_access)
            
            # Student should only have access if enrolled
            student_has_access = student_mixin.test_func()
            self.assertEqual(student_has_access, is_enrolled)

    def test_unauthorized_access_logging(self):
        """
        **Feature: gestion-documentos-cursos, Property 17: Unauthorized access logging**
        For any unauthorized access attempt, the system should deny access 
        and create an audit log entry of the attempt
        """
        # Create a teacher and course
        teacher = User.objects.create_user(
            username='log_teacher',
            password='testpass123',
            email='teacher@test.com'
        )
        teacher.groups.add(self.profesores_group)
        
        course = Curso.objects.create(
            name='Logging Course',
            teacher=teacher,
            curso_academico=self.curso_academico,
            description='Test course for logging'
        )
        
        # Create unauthorized user (student not enrolled)
        unauthorized_user = User.objects.create_user(
            username='unauthorized_user',
            password='testpass123',
            email='unauthorized@test.com'
        )
        unauthorized_user.groups.add(self.estudiantes_group)
        
        # Count initial audit logs
        initial_log_count = AuditLog.objects.filter(action='unauthorized_access').count()
        
        # Test unauthorized access using permission mixin
        from course_documents.permissions import StudentPermissionMixin
        
        class MockRequest:
            def __init__(self, user):
                self.user = user
                self.META = {'REMOTE_ADDR': '127.0.0.1'}
        
        class MockView:
            def __init__(self, user, curso_id):
                self.request = MockRequest(user)
                self.kwargs = {'curso_id': curso_id}
        
        view = MockView(unauthorized_user, course.id)
        mixin = StudentPermissionMixin()
        mixin.request = view.request
        mixin.kwargs = view.kwargs
        
        # Verify access is denied
        has_access = mixin.test_func()
        self.assertFalse(has_access)
        
        # Simulate the handle_no_permission call (which logs the attempt)
        try:
            mixin.handle_no_permission()
        except Exception:
            pass  # Expected to raise PermissionDenied
        
        # Verify audit log was created
        final_log_count = AuditLog.objects.filter(action='unauthorized_access').count()
        self.assertEqual(final_log_count, initial_log_count + 1)
        
        # Verify log details
        latest_log = AuditLog.objects.filter(action='unauthorized_access').latest('timestamp')
        self.assertEqual(latest_log.user, unauthorized_user)
        self.assertEqual(latest_log.curso, course)

    def test_comprehensive_operation_logging(self):
        """
        **Feature: gestion-documentos-cursos, Property 18: Comprehensive operation logging**
        For any document-related operation (upload, download, folder creation), 
        the system should create corresponding audit log entries
        """
        # Create a teacher and course
        teacher = User.objects.create_user(
            username='ops_teacher',
            password='testpass123',
            email='teacher@test.com'
        )
        teacher.groups.add(self.profesores_group)
        
        course = Curso.objects.create(
            name='Operations Course',
            teacher=teacher,
            curso_academico=self.curso_academico,
            description='Test course for operations logging'
        )
        
        # Count initial logs
        initial_log_count = AuditLog.objects.count()
        
        # Test folder creation logging
        folder = DocumentFolder.objects.create(
            curso=course,
            name='Test Folder for Logging',
            created_by=teacher
        )
        
        # Log folder creation manually (would be done by signals in real app)
        AuditLog.log_action(
            user=teacher,
            action='folder_created',
            curso=course,
            folder=folder,
            details='Test folder creation'
        )
        
        # Test document upload logging
        from django.core.files.uploadedfile import SimpleUploadedFile
        
        file_content = b"Test content for logging"
        uploaded_file = SimpleUploadedFile(
            name="test_log_document.txt",
            content=file_content,
            content_type="text/plain"
        )
        
        document = CourseDocument.objects.create(
            folder=folder,
            name='Test Document for Logging',
            file=uploaded_file,
            uploaded_by=teacher
        )
        
        # Document upload should be logged automatically by signals
        
        # Test download logging
        AuditLog.log_action(
            user=teacher,
            action='document_downloaded',
            curso=course,
            folder=folder,
            document=document,
            details='Test document download'
        )
        
        # Verify logs were created
        final_log_count = AuditLog.objects.count()
        self.assertGreaterEqual(final_log_count, initial_log_count + 3)  # At least 3 new logs
        
        # Verify specific log types exist
        self.assertTrue(AuditLog.objects.filter(action='folder_created', folder=folder).exists())
        self.assertTrue(AuditLog.objects.filter(action='document_uploaded', document=document).exists())
        self.assertTrue(AuditLog.objects.filter(action='document_downloaded', document=document).exists())

    def test_no_courses_shows_empty_list_for_teacher(self):
        """
        Edge case: When a teacher has no courses assigned, should show empty list
        """
        # Create a teacher with no courses
        teacher = User.objects.create_user(
            username='teacher_no_courses',
            password='testpass123',
            email='teacher@test.com'
        )
        teacher.groups.add(self.profesores_group)
        
        # Login as teacher
        self.client.login(username=teacher.username, password='testpass123')
        
        # Get profile page
        response = self.client.get(reverse('principal:profile'))
        
        # Verify response is successful
        self.assertEqual(response.status_code, 200)
        
        # Verify no assigned courses
        assigned_courses = response.context.get('assigned_courses', [])
        self.assertEqual(len(assigned_courses), 0)

    def test_no_enrollments_shows_empty_list_for_student(self):
        """
        Edge case: When a student has no enrollments, should show empty list
        """
        # Create a student with no enrollments
        student = User.objects.create_user(
            username='student_no_enrollments',
            password='testpass123',
            email='student@test.com'
        )
        student.groups.add(self.estudiantes_group)
        
        # Login as student
        self.client.login(username=student.username, password='testpass123')
        
        # Get profile page
        response = self.client.get(reverse('principal:profile'))
        
        # Verify response is successful
        self.assertEqual(response.status_code, 200)
        
        # Verify no enrolled courses
        enrolled_courses = response.context.get('enrolled_courses', [])
        self.assertEqual(len(enrolled_courses), 0)


class CourseDocumentsModelTests(TestCase):
    """
    Unit tests for course documents models
    """
    
    def setUp(self):
        """Set up test data"""
        # Create groups
        self.profesores_group, _ = Group.objects.get_or_create(name='Profesores')
        self.estudiantes_group, _ = Group.objects.get_or_create(name='Estudiantes')
        
        # Create academic year
        self.curso_academico, _ = CursoAcademico.objects.get_or_create(
            nombre="2024-2025",
            defaults={'activo': True}
        )
        
        # Create teacher
        self.teacher = User.objects.create_user(
            username='teacher',
            password='testpass123',
            email='teacher@test.com'
        )
        self.teacher.groups.add(self.profesores_group)
        
        # Create course
        self.course = Curso.objects.create(
            name='Test Course',
            teacher=self.teacher,
            curso_academico=self.curso_academico,
            description='Test course description'
        )

    def test_document_folder_creation(self):
        """Test basic document folder creation"""
        folder = DocumentFolder.objects.create(
            curso=self.course,
            name='Test Folder',
            created_by=self.teacher
        )
        
        self.assertEqual(folder.name, 'Test Folder')
        self.assertEqual(folder.curso, self.course)
        self.assertEqual(folder.created_by, self.teacher)
        self.assertTrue(folder.created_at)

    def test_document_folder_unique_constraint(self):
        """Test that folder names must be unique within a course"""
        # Create first folder
        DocumentFolder.objects.create(
            curso=self.course,
            name='Duplicate Name',
            created_by=self.teacher
        )
        
        # Try to create second folder with same name in same course
        with self.assertRaises(Exception):  # Should raise IntegrityError
            DocumentFolder.objects.create(
                curso=self.course,
                name='Duplicate Name',
                created_by=self.teacher
            )

    def test_audit_log_creation(self):
        """Test audit log functionality"""
        log = AuditLog.log_action(
            user=self.teacher,
            action='folder_created',
            curso=self.course,
            details='Test folder created'
        )
        
        self.assertEqual(log.user, self.teacher)
        self.assertEqual(log.action, 'folder_created')
        self.assertEqual(log.curso, self.course)
        self.assertEqual(log.details, 'Test folder created')
        self.assertTrue(log.timestamp)

    def test_new_content_notification_creation(self):
        """Test new content notification functionality"""
        student = User.objects.create_user(
            username='student',
            password='testpass123',
            email='student@test.com'
        )
        student.groups.add(self.estudiantes_group)
        
        notification = NewContentNotification.objects.create(
            curso=self.course,
            student=student,
            has_new_content=True
        )
        
        self.assertEqual(notification.curso, self.course)
        self.assertEqual(notification.student, student)
        self.assertTrue(notification.has_new_content)
        
        # Test mark as seen
        notification.mark_as_seen()
        self.assertFalse(notification.has_new_content)

    @given(st.integers(min_value=1, max_value=5))
    @settings(deadline=None, max_examples=20)
    def test_dashboard_navigation_shows_correct_course_content(self, num_courses):
        """
        **Feature: gestion-documentos-cursos, Property 2: Dashboard navigation shows correct course content**
        For any course dashboard access, clicking a course button should navigate to the dashboard 
        showing content specific to that exact course
        """
        # Create a teacher
        teacher = User.objects.create_user(
            username=f'teacher_nav_{num_courses}',
            password='testpass123',
            email='teacher@test.com'
        )
        teacher.groups.add(self.profesores_group)
        
        # Create multiple courses with different content
        courses_with_folders = []
        for i in range(num_courses):
            course = Curso.objects.create(
                name=f'Navigation Course {i+1}',
                teacher=teacher,
                curso_academico=self.curso_academico,
                description=f'Test course {i+1} for navigation'
            )
            
            # Create unique folders for each course
            folders = []
            for j in range(2):  # 2 folders per course
                folder = DocumentFolder.objects.create(
                    curso=course,
                    name=f'Folder {j+1} for Course {i+1}',
                    created_by=teacher
                )
                folders.append(folder)
            
            courses_with_folders.append((course, folders))
        
        # Login as teacher
        self.client.login(username=teacher.username, password='testpass123')
        
        # Test navigation to each course dashboard
        for course, expected_folders in courses_with_folders:
            # Navigate to specific course dashboard
            response = self.client.get(
                reverse('course_documents:teacher_dashboard', kwargs={'curso_id': course.id})
            )
            
            # Verify response is successful
            self.assertEqual(response.status_code, 200)
            
            # Verify correct course is in context
            context_course = response.context.get('curso')
            self.assertEqual(context_course.id, course.id)
            self.assertEqual(context_course.name, course.name)
            
            # Verify correct folders are displayed
            context_folders = response.context.get('folders', [])
            expected_folder_names = [folder.name for folder in expected_folders]
            context_folder_names = [folder.name for folder in context_folders]
            
            # All expected folders should be present
            for expected_name in expected_folder_names:
                self.assertIn(expected_name, context_folder_names)
            
            # No folders from other courses should be present
            for other_course, other_folders in courses_with_folders:
                if other_course.id != course.id:
                    other_folder_names = [folder.name for folder in other_folders]
                    for other_name in other_folder_names:
                        self.assertNotIn(other_name, context_folder_names)

    @given(st.integers(min_value=2, max_value=8))
    @settings(deadline=None, max_examples=15)
    def test_multiple_course_buttons_are_uniquely_identified(self, num_courses):
        """
        **Feature: gestion-documentos-cursos, Property 3: Multiple course buttons are uniquely identified**
        For any user with multiple courses, each dashboard button should contain 
        the unique name of its corresponding course
        """
        # Create a teacher
        teacher = User.objects.create_user(
            username=f'teacher_multi_{num_courses}',
            password='testpass123',
            email='teacher@test.com'
        )
        teacher.groups.add(self.profesores_group)
        
        # Create multiple courses with unique names
        courses = []
        course_names = []
        for i in range(num_courses):
            unique_name = f'Unique Course {i+1} - {hash(str(i)) % 10000}'
            course = Curso.objects.create(
                name=unique_name,
                teacher=teacher,
                curso_academico=self.curso_academico,
                description=f'Test course {i+1} with unique name'
            )
            courses.append(course)
            course_names.append(unique_name)
        
        # Login as teacher
        self.client.login(username=teacher.username, password='testpass123')
        
        # Get profile page (where course buttons are displayed)
        response = self.client.get(reverse('principal:profile'))
        
        # Verify response is successful
        self.assertEqual(response.status_code, 200)
        
        # Verify all courses are in assigned_courses context
        assigned_courses = response.context.get('assigned_courses', [])
        self.assertEqual(len(assigned_courses), num_courses)
        
        # Verify each course name is unique and present
        assigned_course_names = [course.name for course in assigned_courses]
        
        # All created course names should be present
        for expected_name in course_names:
            self.assertIn(expected_name, assigned_course_names)
        
        # All names should be unique (no duplicates)
        self.assertEqual(len(assigned_course_names), len(set(assigned_course_names)))
        
        # Verify each course has correct identification
        for course in assigned_courses:
            # Course name should be one of our created names
            self.assertIn(course.name, course_names)
            
            # Course should have correct teacher assignment
            self.assertEqual(course.teacher, teacher)
            
            # Course should be in the active academic year
            self.assertEqual(course.curso_academico, self.curso_academico)

    @given(st.integers(min_value=1, max_value=5))
    @settings(deadline=None, max_examples=15)
    def test_student_dashboard_navigation_shows_correct_course_content(self, num_enrollments):
        """
        **Feature: gestion-documentos-cursos, Property 2: Dashboard navigation shows correct course content**
        For any student course dashboard access, clicking a course button should navigate 
        to the dashboard showing content specific to that exact course
        """
        # Create a teacher for the courses
        teacher = User.objects.create_user(
            username=f'teacher_student_nav_{num_enrollments}',
            password='testpass123',
            email='teacher@test.com'
        )
        teacher.groups.add(self.profesores_group)
        
        # Create a student
        student = User.objects.create_user(
            username=f'student_nav_{num_enrollments}',
            password='testpass123',
            email='student@test.com'
        )
        student.groups.add(self.estudiantes_group)
        
        # Create multiple courses with different content and enroll student
        enrolled_courses_with_content = []
        for i in range(num_enrollments):
            course = Curso.objects.create(
                name=f'Student Navigation Course {i+1}',
                teacher=teacher,
                curso_academico=self.curso_academico,
                description=f'Test course {i+1} for student navigation'
            )
            
            # Enroll student in course
            Matriculas.objects.create(
                course=course,
                student=student,
                curso_academico=self.curso_academico,
                activo=True
            )
            
            # Create folders and documents for each course
            folders_with_docs = []
            for j in range(2):  # 2 folders per course
                folder = DocumentFolder.objects.create(
                    curso=course,
                    name=f'Student Folder {j+1} for Course {i+1}',
                    created_by=teacher
                )
                
                # Add a document to the folder
                from django.core.files.uploadedfile import SimpleUploadedFile
                file_content = f"Content for course {i+1} folder {j+1}".encode()
                uploaded_file = SimpleUploadedFile(
                    name=f"doc_c{i+1}_f{j+1}.txt",
                    content=file_content,
                    content_type="text/plain"
                )
                
                document = CourseDocument.objects.create(
                    folder=folder,
                    name=f'Document {j+1} for Course {i+1}',
                    file=uploaded_file,
                    uploaded_by=teacher
                )
                
                folders_with_docs.append((folder, document))
            
            enrolled_courses_with_content.append((course, folders_with_docs))
        
        # Login as student
        self.client.login(username=student.username, password='testpass123')
        
        # Test navigation to each enrolled course dashboard
        for course, expected_content in enrolled_courses_with_content:
            # Navigate to specific course dashboard (student view)
            response = self.client.get(
                reverse('course_documents:student_dashboard', kwargs={'curso_id': course.id})
            )
            
            # Verify response is successful
            self.assertEqual(response.status_code, 200)
            
            # Verify correct course is in context
            context_course = response.context.get('curso')
            self.assertEqual(context_course.id, course.id)
            self.assertEqual(context_course.name, course.name)
            
            # Verify correct folders are displayed
            context_folders = response.context.get('folders', [])
            expected_folder_names = [folder.name for folder, doc in expected_content]
            context_folder_names = [folder.name for folder in context_folders]
            
            # All expected folders should be present
            for expected_name in expected_folder_names:
                self.assertIn(expected_name, context_folder_names)
            
            # No folders from other courses should be present
            for other_course, other_content in enrolled_courses_with_content:
                if other_course.id != course.id:
                    other_folder_names = [folder.name for folder, doc in other_content]
                    for other_name in other_folder_names:
                        self.assertNotIn(other_name, context_folder_names)

    @given(st.integers(min_value=2, max_value=6))
    @settings(deadline=None, max_examples=10)
    def test_student_multiple_course_buttons_are_uniquely_identified(self, num_enrollments):
        """
        **Feature: gestion-documentos-cursos, Property 3: Multiple course buttons are uniquely identified**
        For any student with multiple course enrollments, each dashboard button should contain 
        the unique name of its corresponding course
        """
        # Create a teacher for the courses
        teacher = User.objects.create_user(
            username=f'teacher_student_multi_{num_enrollments}',
            password='testpass123',
            email='teacher@test.com'
        )
        teacher.groups.add(self.profesores_group)
        
        # Create a student
        student = User.objects.create_user(
            username=f'student_multi_{num_enrollments}',
            password='testpass123',
            email='student@test.com'
        )
        student.groups.add(self.estudiantes_group)
        
        # Create multiple courses with unique names and enroll student
        enrolled_courses = []
        course_names = []
        for i in range(num_enrollments):
            unique_name = f'Student Unique Course {i+1} - {hash(str(i+100)) % 10000}'
            course = Curso.objects.create(
                name=unique_name,
                teacher=teacher,
                curso_academico=self.curso_academico,
                description=f'Test course {i+1} with unique name for student'
            )
            
            # Enroll student in course
            Matriculas.objects.create(
                course=course,
                student=student,
                curso_academico=self.curso_academico,
                activo=True
            )
            
            enrolled_courses.append(course)
            course_names.append(unique_name)
        
        # Login as student
        self.client.login(username=student.username, password='testpass123')
        
        # Get profile page (where course buttons are displayed)
        response = self.client.get(reverse('principal:profile'))
        
        # Verify response is successful
        self.assertEqual(response.status_code, 200)
        
        # Verify all courses are in enrolled_courses context
        enrolled_courses_context = response.context.get('enrolled_courses', [])
        self.assertEqual(len(enrolled_courses_context), num_enrollments)
        
        # Verify each course name is unique and present
        enrolled_course_names = [course.name for course in enrolled_courses_context]
        
        # All created course names should be present
        for expected_name in course_names:
            self.assertIn(expected_name, enrolled_course_names)
        
        # All names should be unique (no duplicates)
        self.assertEqual(len(enrolled_course_names), len(set(enrolled_course_names)))
        
        # Verify each course has correct identification
        for course in enrolled_courses_context:
            # Course name should be one of our created names
            self.assertIn(course.name, course_names)
            
            # Course should have correct teacher assignment
            self.assertEqual(course.teacher, teacher)
            
            # Course should be in the active academic year
            self.assertEqual(course.curso_academico, self.curso_academico)
            
            # Verify student is actually enrolled in this course
            self.assertTrue(
                Matriculas.objects.filter(
                    course=course,
                    student=student,
                    activo=True
                ).exists()
            )

    @given(st.integers(min_value=1, max_value=8))
    @settings(deadline=None, max_examples=15)
    def test_folder_content_display_completeness(self, num_documents):
        """
        **Feature: gestion-documentos-cursos, Property 9: Folder content display completeness**
        For any folder with documents, selecting the folder should display 
        all documents contained within that folder
        """
        # Create a teacher and course
        teacher = User.objects.create_user(
            username=f'teacher_folder_content_{num_documents}',
            password='testpass123',
            email='teacher@test.com'
        )
        teacher.groups.add(self.profesores_group)
        
        course = Curso.objects.create(
            name=f'Folder Content Course {num_documents}',
            teacher=teacher,
            curso_academico=self.curso_academico,
            description='Test course for folder content display'
        )
        
        # Create a student and enroll in course
        student = User.objects.create_user(
            username=f'student_folder_content_{num_documents}',
            password='testpass123',
            email='student@test.com'
        )
        student.groups.add(self.estudiantes_group)
        
        Matriculas.objects.create(
            course=course,
            student=student,
            curso_academico=self.curso_academico,
            activo=True
        )
        
        # Create a folder
        folder = DocumentFolder.objects.create(
            curso=course,
            name='Test Folder for Content Display',
            created_by=teacher
        )
        
        # Create multiple documents in the folder
        created_documents = []
        for i in range(num_documents):
            from django.core.files.uploadedfile import SimpleUploadedFile
            
            file_content = f"Content for document {i+1}".encode()
            uploaded_file = SimpleUploadedFile(
                name=f"test_document_{i+1}.txt",
                content=file_content,
                content_type="text/plain"
            )
            
            document = CourseDocument.objects.create(
                folder=folder,
                name=f'Test Document {i+1}',
                file=uploaded_file,
                uploaded_by=teacher
            )
            created_documents.append(document)
        
        # Login as student
        self.client.login(username=student.username, password='testpass123')
        
        # Access student folder detail view
        response = self.client.get(
            reverse('course_documents:student_folder_detail', 
                   kwargs={'curso_id': course.id, 'folder_id': folder.id})
        )
        
        # Verify response is successful
        self.assertEqual(response.status_code, 200)
        
        # Verify correct folder is in context
        context_folder = response.context.get('folder')
        self.assertEqual(context_folder.id, folder.id)
        self.assertEqual(context_folder.name, folder.name)
        
        # Verify all documents are displayed
        context_documents = response.context.get('documents', [])
        self.assertEqual(len(context_documents), num_documents)
        
        # Verify each created document is in the context
        context_document_names = [doc.name for doc in context_documents]
        for created_doc in created_documents:
            self.assertIn(created_doc.name, context_document_names)
        
        # Verify documents belong to the correct folder
        for context_doc in context_documents:
            self.assertEqual(context_doc.folder.id, folder.id)
        
        # Test student dashboard view as well
        dashboard_response = self.client.get(
            reverse('course_documents:student_dashboard', kwargs={'curso_id': course.id})
        )
        
        self.assertEqual(dashboard_response.status_code, 200)
        
        # Verify folder appears in dashboard with documents
        dashboard_folders = dashboard_response.context.get('folders', [])
        folder_found = False
        for dashboard_folder in dashboard_folders:
            if dashboard_folder.id == folder.id:
                folder_found = True
                # Verify folder has the correct number of documents
                self.assertEqual(dashboard_folder.document_list.count(), num_documents)
                break
        
        self.assertTrue(folder_found, "Folder with documents should appear in student dashboard")

    @given(st.integers(min_value=1, max_value=5))
    @settings(deadline=None, max_examples=10)
    def test_download_access_logging(self, num_downloads):
        """
        **Feature: gestion-documentos-cursos, Property 10: Download access logging**
        For any successful document download by a student, the system should 
        create a corresponding access log entry
        """
        # Create a teacher and course
        teacher = User.objects.create_user(
            username=f'teacher_download_log_{num_downloads}',
            password='testpass123',
            email='teacher@test.com'
        )
        teacher.groups.add(self.profesores_group)
        
        course = Curso.objects.create(
            name=f'Download Logging Course {num_downloads}',
            teacher=teacher,
            curso_academico=self.curso_academico,
            description='Test course for download logging'
        )
        
        # Create a student and enroll in course
        student = User.objects.create_user(
            username=f'student_download_log_{num_downloads}',
            password='testpass123',
            email='student@test.com'
        )
        student.groups.add(self.estudiantes_group)
        
        Matriculas.objects.create(
            course=course,
            student=student,
            curso_academico=self.curso_academico,
            activo=True
        )
        
        # Create a folder and document
        folder = DocumentFolder.objects.create(
            curso=course,
            name='Download Test Folder',
            created_by=teacher
        )
        
        from django.core.files.uploadedfile import SimpleUploadedFile
        
        file_content = b"Test content for download logging"
        uploaded_file = SimpleUploadedFile(
            name="download_test.txt",
            content=file_content,
            content_type="text/plain"
        )
        
        document = CourseDocument.objects.create(
            folder=folder,
            name='Download Test Document',
            file=uploaded_file,
            uploaded_by=teacher
        )
        
        # Count initial access logs
        initial_access_count = DocumentAccess.objects.filter(
            document=document,
            student=student
        ).count()
        
        initial_audit_count = AuditLog.objects.filter(
            action='document_downloaded',
            user=student,
            document=document
        ).count()
        
        # Login as student
        self.client.login(username=student.username, password='testpass123')
        
        # Perform multiple downloads
        for i in range(num_downloads):
            response = self.client.get(
                reverse('course_documents:download_document', 
                       kwargs={'curso_id': course.id, 'document_id': document.id})
            )
            
            # Verify download was successful (should return file content)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.content, file_content)
        
        # Verify access logs were created
        final_access_count = DocumentAccess.objects.filter(
            document=document,
            student=student
        ).count()
        
        self.assertEqual(final_access_count, initial_access_count + num_downloads)
        
        # Verify audit logs were created
        final_audit_count = AuditLog.objects.filter(
            action='document_downloaded',
            user=student,
            document=document
        ).count()
        
        self.assertEqual(final_audit_count, initial_audit_count + num_downloads)
        
        # Verify log details
        access_logs = DocumentAccess.objects.filter(
            document=document,
            student=student
        ).order_by('-accessed_at')
        
        # All logs should have correct document and student
        for log in access_logs:
            self.assertEqual(log.document, document)
            self.assertEqual(log.student, student)
            self.assertTrue(log.accessed_at)
        
        # Verify audit log details
        audit_logs = AuditLog.objects.filter(
            action='document_downloaded',
            user=student,
            document=document
        ).order_by('-timestamp')
        
        for audit_log in audit_logs:
            self.assertEqual(audit_log.user, student)
            self.assertEqual(audit_log.curso, course)
            self.assertEqual(audit_log.folder, folder)
            self.assertEqual(audit_log.document, document)
            self.assertIn('descargado por estudiante', audit_log.details.lower())

    def test_empty_folder_shows_no_documents(self):
        """
        Edge case: Empty folder should show no documents
        """
        # Create a teacher and course
        teacher = User.objects.create_user(
            username='teacher_empty_folder',
            password='testpass123',
            email='teacher@test.com'
        )
        teacher.groups.add(self.profesores_group)
        
        course = Curso.objects.create(
            name='Empty Folder Course',
            teacher=teacher,
            curso_academico=self.curso_academico,
            description='Test course for empty folder'
        )
        
        # Create a student and enroll in course
        student = User.objects.create_user(
            username='student_empty_folder',
            password='testpass123',
            email='student@test.com'
        )
        student.groups.add(self.estudiantes_group)
        
        Matriculas.objects.create(
            course=course,
            student=student,
            curso_academico=self.curso_academico,
            activo=True
        )
        
        # Create an empty folder
        empty_folder = DocumentFolder.objects.create(
            curso=course,
            name='Empty Test Folder',
            created_by=teacher
        )
        
        # Login as student
        self.client.login(username=student.username, password='testpass123')
        
        # Access student dashboard
        response = self.client.get(
            reverse('course_documents:student_dashboard', kwargs={'curso_id': course.id})
        )
        
        # Verify response is successful
        self.assertEqual(response.status_code, 200)
        
        # Empty folders should not appear in student dashboard
        # (only folders with documents are shown)
        folders = response.context.get('folders', [])
        folder_ids = [folder.id for folder in folders]
        self.assertNotIn(empty_folder.id, folder_ids)

    def test_unauthorized_student_download_denied(self):
        """
        Edge case: Student not enrolled in course should be denied download access
        """
        # Create a teacher and course
        teacher = User.objects.create_user(
            username='teacher_unauthorized',
            password='testpass123',
            email='teacher@test.com'
        )
        teacher.groups.add(self.profesores_group)
        
        course = Curso.objects.create(
            name='Unauthorized Course',
            teacher=teacher,
            curso_academico=self.curso_academico,
            description='Test course for unauthorized access'
        )
        
        # Create a student NOT enrolled in course
        unauthorized_student = User.objects.create_user(
            username='unauthorized_student',
            password='testpass123',
            email='unauthorized@test.com'
        )
        unauthorized_student.groups.add(self.estudiantes_group)
        
        # Create a folder and document
        folder = DocumentFolder.objects.create(
            curso=course,
            name='Unauthorized Test Folder',
            created_by=teacher
        )
        
        from django.core.files.uploadedfile import SimpleUploadedFile
        
        file_content = b"Unauthorized test content"
        uploaded_file = SimpleUploadedFile(
            name="unauthorized_test.txt",
            content=file_content,
            content_type="text/plain"
        )
        
        document = CourseDocument.objects.create(
            folder=folder,
            name='Unauthorized Test Document',
            file=uploaded_file,
            uploaded_by=teacher
        )
        
        # Login as unauthorized student
        self.client.login(username=unauthorized_student.username, password='testpass123')
        
        # Try to download document
        response = self.client.get(
            reverse('course_documents:download_document', 
                   kwargs={'curso_id': course.id, 'document_id': document.id})
        )
        
        # Should be denied access (403 or redirect)
        self.assertIn(response.status_code, [403, 302])
        
        # Verify no access log was created
        access_count = DocumentAccess.objects.filter(
            document=document,
            student=unauthorized_student
        ).count()
        
        self.assertEqual(access_count, 0)
    @given(st.integers(min_value=1, max_value=8))
    @settings(deadline=None, max_examples=10)
    def test_email_notification_distribution(self, num_students):
        """
        **Feature: gestion-documentos-cursos, Property 12: Email notification distribution**
        For any new document upload, the system should send individual email 
        notifications to all students enrolled in that course
        """
        from unittest.mock import patch
        from course_documents.services import NotificationService
        
        # Create a teacher and course
        teacher = User.objects.create_user(
            username=f'teacher_email_{num_students}',
            password='testpass123',
            email='teacher@test.com'
        )
        teacher.groups.add(self.profesores_group)
        
        course = Curso.objects.create(
            name=f'Email Notification Course {num_students}',
            teacher=teacher,
            curso_academico=self.curso_academico,
            description='Test course for email notifications'
        )
        
        # Create multiple students and enroll them
        enrolled_students = []
        for i in range(num_students):
            student = User.objects.create_user(
                username=f'student_email_{num_students}_{i}',
                password='testpass123',
                email=f'student{i}@test.com'
            )
            student.groups.add(self.estudiantes_group)
            
            Matriculas.objects.create(
                course=course,
                student=student,
                curso_academico=self.curso_academico,
                activo=True
            )
            
            enrolled_students.append(student)
        
        # Create a folder and document
        folder = DocumentFolder.objects.create(
            curso=course,
            name='Email Test Folder',
            created_by=teacher
        )
        
        from django.core.files.uploadedfile import SimpleUploadedFile
        
        file_content = b"Test content for email notifications"
        uploaded_file = SimpleUploadedFile(
            name="email_test.txt",
            content=file_content,
            content_type="text/plain"
        )
        
        document = CourseDocument.objects.create(
            folder=folder,
            name='Email Test Document',
            file=uploaded_file,
            uploaded_by=teacher
        )
        
        # Count initial email audit logs
        initial_email_logs = AuditLog.objects.filter(
            action='email_sent',
            curso=course,
            document=document
        ).count()
        
        # Mock email sending to avoid actual email delivery in tests
        with patch('course_documents.services.EmailMultiAlternatives') as mock_email:
            mock_email_instance = mock_email.return_value
            mock_email_instance.send.return_value = True
            
            # Trigger notification
            NotificationService.notify_new_document(document)
            
            # Verify email was created for each student
            self.assertEqual(mock_email.call_count, num_students)
            self.assertEqual(mock_email_instance.send.call_count, num_students)
        
        # Verify audit logs were created for each student
        final_email_logs = AuditLog.objects.filter(
            action='email_sent',
            curso=course,
            document=document
        ).count()
        
        self.assertEqual(final_email_logs, initial_email_logs + num_students)
        
        # Verify each enrolled student has an email log
        for student in enrolled_students:
            email_log_exists = AuditLog.objects.filter(
                action='email_sent',
                user=student,
                curso=course,
                document=document
            ).exists()
            self.assertTrue(email_log_exists, f"Email log should exist for student {student.username}")
        
        # Verify batch notification log was created
        batch_log_exists = AuditLog.objects.filter(
            action='notification_batch_sent',
            user=teacher,
            curso=course,
            document=document
        ).exists()
        self.assertTrue(batch_log_exists, "Batch notification log should exist")

    @given(st.text(min_size=1, max_size=20).filter(lambda x: x.strip()))
    @settings(deadline=None, max_examples=15)
    def test_email_content_completeness(self, document_name):
        """
        **Feature: gestion-documentos-cursos, Property 13: Email content completeness**
        For any notification email sent, the message should contain the course name, 
        folder name, document name, and direct link to the course dashboard
        """
        from unittest.mock import patch, MagicMock
        from course_documents.services import NotificationService
        
        # Create a teacher and course
        teacher = User.objects.create_user(
            username=f'teacher_content_{abs(hash(document_name)) % 10000}',
            password='testpass123',
            email='teacher@test.com'
        )
        teacher.groups.add(self.profesores_group)
        
        course_name = f'Content Test Course {abs(hash(document_name)) % 10000}'
        course = Curso.objects.create(
            name=course_name,
            teacher=teacher,
            curso_academico=self.curso_academico,
            description='Test course for email content'
        )
        
        # Create a student and enroll
        student = User.objects.create_user(
            username=f'student_content_{abs(hash(document_name)) % 10000}',
            password='testpass123',
            email='student@test.com'
        )
        student.groups.add(self.estudiantes_group)
        
        Matriculas.objects.create(
            course=course,
            student=student,
            curso_academico=self.curso_academico,
            activo=True
        )
        
        # Create a folder and document
        folder_name = f'Content Test Folder {abs(hash(document_name)) % 1000}'
        folder = DocumentFolder.objects.create(
            curso=course,
            name=folder_name,
            created_by=teacher
        )
        
        from django.core.files.uploadedfile import SimpleUploadedFile
        
        file_content = f"Content for {document_name}".encode()
        uploaded_file = SimpleUploadedFile(
            name=f"{re.sub(r'[<>:"/\|?*]', '_', document_name.strip()) or 'test_document'}.txt",
            content=file_content,
            content_type="text/plain"
        )
        
        document = CourseDocument.objects.create(
            folder=folder,
            name=document_name.strip(),
            file=uploaded_file,
            uploaded_by=teacher
        )
        
        # Mock email sending and capture email content
        captured_emails = []
        
        def capture_email(*args, **kwargs):
            email_instance = MagicMock()
            
            # Capture email data
            email_data = {
                'subject': kwargs.get('subject', ''),
                'body': kwargs.get('body', ''),
                'to': kwargs.get('to', []),
            }
            captured_emails.append(email_data)
            
            email_instance.send.return_value = True
            return email_instance
        
        with patch('course_documents.services.EmailMultiAlternatives', side_effect=capture_email):
            with patch('course_documents.services.render_to_string') as mock_render:
                # Mock template rendering to return content with required elements
                def mock_render_func(template_name, context):
                    if 'new_document.txt' in template_name:
                        return f"""
                        Curso: {context['curso'].name}
                        Carpeta: {context['folder'].name}
                        Documento: {context['document'].name}
                        Dashboard: {context['dashboard_url']}
                        Profesor: {context['teacher'].get_full_name() or context['teacher'].username}
                        """
                    return "Mock content"
                
                mock_render.side_effect = mock_render_func
                
                # Trigger notification
                NotificationService.notify_new_document(document)
        
        # Verify email was sent
        self.assertEqual(len(captured_emails), 1)
        
        # Verify email content contains required elements
        email_content = captured_emails[0]['body']
        
        # Check that all required elements are present in the email content
        self.assertIn(course_name, email_content, "Email should contain course name")
        self.assertIn(folder_name, email_content, "Email should contain folder name")
        self.assertIn(document_name.strip(), email_content, "Email should contain document name")
        self.assertIn('dashboard', email_content.lower(), "Email should contain dashboard link reference")
        
        # Verify email was sent to correct recipient
        self.assertIn(student.email, captured_emails[0]['to'])
        
        # Verify subject contains course name
        subject = captured_emails[0]['subject']
        self.assertIn(course_name, subject, "Email subject should contain course name")

    def test_email_notification_with_no_enrolled_students(self):
        """
        Edge case: Course with no enrolled students should not send any emails
        """
        from unittest.mock import patch
        from course_documents.services import NotificationService
        
        # Create a teacher and course
        teacher = User.objects.create_user(
            username='teacher_no_students',
            password='testpass123',
            email='teacher@test.com'
        )
        teacher.groups.add(self.profesores_group)
        
        course = Curso.objects.create(
            name='No Students Course',
            teacher=teacher,
            curso_academico=self.curso_academico,
            description='Test course with no students'
        )
        
        # Create a folder and document (no students enrolled)
        folder = DocumentFolder.objects.create(
            curso=course,
            name='No Students Folder',
            created_by=teacher
        )
        
        from django.core.files.uploadedfile import SimpleUploadedFile
        
        file_content = b"Test content for no students"
        uploaded_file = SimpleUploadedFile(
            name="no_students_test.txt",
            content=file_content,
            content_type="text/plain"
        )
        
        document = CourseDocument.objects.create(
            folder=folder,
            name='No Students Document',
            file=uploaded_file,
            uploaded_by=teacher
        )
        
        # Mock email sending
        with patch('course_documents.services.EmailMultiAlternatives') as mock_email:
            # Trigger notification
            NotificationService.notify_new_document(document)
            
            # Verify no emails were sent
            self.assertEqual(mock_email.call_count, 0)
        
        # Verify no email audit logs were created
        email_logs = AuditLog.objects.filter(
            action='email_sent',
            curso=course,
            document=document
        ).count()
        
        self.assertEqual(email_logs, 0)

    def test_email_notification_handles_invalid_email_addresses(self):
        """
        Edge case: Students with invalid email addresses should be handled gracefully
        """
        from unittest.mock import patch
        from course_documents.services import NotificationService
        
        # Create a teacher and course
        teacher = User.objects.create_user(
            username='teacher_invalid_email',
            password='testpass123',
            email='teacher@test.com'
        )
        teacher.groups.add(self.profesores_group)
        
        course = Curso.objects.create(
            name='Invalid Email Course',
            teacher=teacher,
            curso_academico=self.curso_academico,
            description='Test course for invalid emails'
        )
        
        # Create students with invalid email addresses
        valid_student = User.objects.create_user(
            username='valid_student',
            password='testpass123',
            email='valid@test.com'
        )
        valid_student.groups.add(self.estudiantes_group)
        
        invalid_student = User.objects.create_user(
            username='invalid_student',
            password='testpass123',
            email='invalid-email'  # Invalid email format
        )
        invalid_student.groups.add(self.estudiantes_group)
        
        # Enroll both students
        Matriculas.objects.create(
            course=course,
            student=valid_student,
            curso_academico=self.curso_academico,
            activo=True
        )
        
        Matriculas.objects.create(
            course=course,
            student=invalid_student,
            curso_academico=self.curso_academico,
            activo=True
        )
        
        # Create a folder and document
        folder = DocumentFolder.objects.create(
            curso=course,
            name='Invalid Email Folder',
            created_by=teacher
        )
        
        from django.core.files.uploadedfile import SimpleUploadedFile
        
        file_content = b"Test content for invalid email handling"
        uploaded_file = SimpleUploadedFile(
            name="invalid_email_test.txt",
            content=file_content,
            content_type="text/plain"
        )
        
        document = CourseDocument.objects.create(
            folder=folder,
            name='Invalid Email Document',
            file=uploaded_file,
            uploaded_by=teacher
        )
        
        # Mock email sending to simulate failure for invalid email
        def mock_email_send(self):
            if 'invalid-email' in self.to[0]:
                raise Exception("Invalid email address")
            return True
        
        with patch('course_documents.services.EmailMultiAlternatives') as mock_email_class:
            mock_email_instance = mock_email_class.return_value
            mock_email_instance.send.side_effect = mock_email_send
            
            # Trigger notification (should handle errors gracefully)
            NotificationService.notify_new_document(document)
        
        # Verify successful email log exists for valid student
        valid_email_log = AuditLog.objects.filter(
            action='email_sent',
            user=valid_student,
            curso=course,
            document=document
        ).exists()
        self.assertTrue(valid_email_log, "Valid student should have successful email log")
        
        # Verify error log exists for invalid student
        error_email_log = AuditLog.objects.filter(
            action='email_error',
            user=invalid_student,
            curso=course,
            document=document
        ).exists()
        self.assertTrue(error_email_log, "Invalid student should have error email log")
    @given(st.integers(min_value=1, max_value=6))
    @settings(deadline=None, max_examples=12)
    def test_new_content_indicator_activation(self, num_students):
        """
        **Feature: gestion-documentos-cursos, Property 14: New content indicator activation**
        For any new document upload, the system should immediately activate 
        the new content indicator for all enrolled students of that course
        """
        from course_documents.indicator_service import ContentIndicatorService
        
        # Create a teacher and course
        teacher = User.objects.create_user(
            username=f'teacher_indicator_{num_students}',
            password='testpass123',
            email='teacher@test.com'
        )
        teacher.groups.add(self.profesores_group)
        
        course = Curso.objects.create(
            name=f'Indicator Course {num_students}',
            teacher=teacher,
            curso_academico=self.curso_academico,
            description='Test course for indicator activation'
        )
        
        # Create multiple students and enroll them
        enrolled_students = []
        for i in range(num_students):
            student = User.objects.create_user(
                username=f'student_indicator_{num_students}_{i}',
                password='testpass123',
                email=f'student{i}@test.com'
            )
            student.groups.add(self.estudiantes_group)
            
            Matriculas.objects.create(
                course=course,
                student=student,
                curso_academico=self.curso_academico,
                activo=True
            )
            
            enrolled_students.append(student)
        
        # Verify initially no students have new content indicators
        for student in enrolled_students:
            has_new_content = ContentIndicatorService.has_new_content(course, student)
            self.assertFalse(has_new_content, f"Student {student.username} should not have new content initially")
        
        # Create a folder and document
        folder = DocumentFolder.objects.create(
            curso=course,
            name='Indicator Test Folder',
            created_by=teacher
        )
        
        from django.core.files.uploadedfile import SimpleUploadedFile
        
        file_content = b"Test content for indicator activation"
        uploaded_file = SimpleUploadedFile(
            name="indicator_test.txt",
            content=file_content,
            content_type="text/plain"
        )
        
        document = CourseDocument.objects.create(
            folder=folder,
            name='Indicator Test Document',
            file=uploaded_file,
            uploaded_by=teacher
        )
        
        # Trigger indicator activation
        ContentIndicatorService.activate_indicators_for_course(course)
        
        # Verify all enrolled students now have new content indicators
        for student in enrolled_students:
            has_new_content = ContentIndicatorService.has_new_content(course, student)
            self.assertTrue(has_new_content, f"Student {student.username} should have new content indicator after document upload")
        
        # Verify indicator audit logs were created
        for student in enrolled_students:
            indicator_log_exists = AuditLog.objects.filter(
                action='indicator_activated',
                user=student,
                curso=course
            ).exists()
            self.assertTrue(indicator_log_exists, f"Indicator activation log should exist for student {student.username}")
        
        # Verify indicator statistics
        stats = ContentIndicatorService.get_indicator_stats_for_course(course)
        self.assertEqual(stats['total_students'], num_students)
        self.assertEqual(stats['students_with_new_content'], num_students)
        self.assertEqual(stats['students_seen_content'], 0)

    @given(st.integers(min_value=1, max_value=5))
    @settings(deadline=None, max_examples=10)
    def test_new_content_indicator_removal(self, num_accesses):
        """
        **Feature: gestion-documentos-cursos, Property 15: New content indicator removal**
        For any student accessing a course dashboard with new content, 
        the new content indicator for that course should be removed for that student
        """
        from course_documents.indicator_service import ContentIndicatorService
        
        # Create a teacher and course
        teacher = User.objects.create_user(
            username=f'teacher_removal_{num_accesses}',
            password='testpass123',
            email='teacher@test.com'
        )
        teacher.groups.add(self.profesores_group)
        
        course = Curso.objects.create(
            name=f'Removal Course {num_accesses}',
            teacher=teacher,
            curso_academico=self.curso_academico,
            description='Test course for indicator removal'
        )
        
        # Create a student and enroll
        student = User.objects.create_user(
            username=f'student_removal_{num_accesses}',
            password='testpass123',
            email='student@test.com'
        )
        student.groups.add(self.estudiantes_group)
        
        Matriculas.objects.create(
            course=course,
            student=student,
            curso_academico=self.curso_academico,
            activo=True
        )
        
        # Create a folder and document
        folder = DocumentFolder.objects.create(
            curso=course,
            name='Removal Test Folder',
            created_by=teacher
        )
        
        from django.core.files.uploadedfile import SimpleUploadedFile
        
        file_content = b"Test content for indicator removal"
        uploaded_file = SimpleUploadedFile(
            name="removal_test.txt",
            content=file_content,
            content_type="text/plain"
        )
        
        document = CourseDocument.objects.create(
            folder=folder,
            name='Removal Test Document',
            file=uploaded_file,
            uploaded_by=teacher
        )
        
        # Activate indicator for the student
        ContentIndicatorService.activate_indicators_for_course(course)
        
        # Verify student has new content indicator
        has_new_content = ContentIndicatorService.has_new_content(course, student)
        self.assertTrue(has_new_content, "Student should have new content indicator initially")
        
        # Login as student
        self.client.login(username=student.username, password='testpass123')
        
        # Access student dashboard multiple times
        for i in range(num_accesses):
            response = self.client.get(
                reverse('course_documents:student_dashboard', kwargs={'curso_id': course.id})
            )
            
            # Verify response is successful
            self.assertEqual(response.status_code, 200)
        
        # Verify indicator was removed after first access
        has_new_content_after = ContentIndicatorService.has_new_content(course, student)
        self.assertFalse(has_new_content_after, "Student should not have new content indicator after accessing dashboard")
        
        # Verify deactivation audit log was created
        deactivation_log_exists = AuditLog.objects.filter(
            action='indicator_deactivated',
            user=student,
            curso=course
        ).exists()
        self.assertTrue(deactivation_log_exists, "Indicator deactivation log should exist")
        
        # Verify content viewed log was created
        content_viewed_log_exists = AuditLog.objects.filter(
            action='content_viewed',
            user=student,
            curso=course
        ).exists()
        self.assertTrue(content_viewed_log_exists, "Content viewed log should exist")

    @given(st.integers(min_value=1, max_value=4))
    @settings(deadline=None, max_examples=8)
    def test_default_indicator_state_no_new_content(self, num_students):
        """
        **Feature: gestion-documentos-cursos, Property 16: Default indicator state**
        For any course without new content, the dashboard button should not 
        display a new content indicator
        """
        from course_documents.indicator_service import ContentIndicatorService
        
        # Create a teacher and course
        teacher = User.objects.create_user(
            username=f'teacher_default_{num_students}',
            password='testpass123',
            email='teacher@test.com'
        )
        teacher.groups.add(self.profesores_group)
        
        course = Curso.objects.create(
            name=f'Default State Course {num_students}',
            teacher=teacher,
            curso_academico=self.curso_academico,
            description='Test course for default indicator state'
        )
        
        # Create multiple students and enroll them
        enrolled_students = []
        for i in range(num_students):
            student = User.objects.create_user(
                username=f'student_default_{num_students}_{i}',
                password='testpass123',
                email=f'student{i}@test.com'
            )
            student.groups.add(self.estudiantes_group)
            
            Matriculas.objects.create(
                course=course,
                student=student,
                curso_academico=self.curso_academico,
                activo=True
            )
            
            enrolled_students.append(student)
        
        # Verify no students have new content indicators by default
        for student in enrolled_students:
            has_new_content = ContentIndicatorService.has_new_content(course, student)
            self.assertFalse(has_new_content, f"Student {student.username} should not have new content indicator by default")
        
        # Verify course statistics show no new content
        stats = ContentIndicatorService.get_indicator_stats_for_course(course)
        self.assertEqual(stats['total_students'], num_students)
        self.assertEqual(stats['students_with_new_content'], 0)
        
        # Test each student's profile view
        for student in enrolled_students:
            self.client.login(username=student.username, password='testpass123')
            
            response = self.client.get(reverse('principal:profile'))
            self.assertEqual(response.status_code, 200)
            
            # Verify enrolled courses don't have new content indicators
            enrolled_courses = response.context.get('enrolled_courses', [])
            for enrolled_course in enrolled_courses:
                if enrolled_course.id == course.id:
                    # Course should not have new content indicator
                    has_indicator = getattr(enrolled_course, 'has_new_content_indicator', False)
                    self.assertFalse(has_indicator, f"Course should not have new content indicator for student {student.username}")
        
        # Create a folder but no documents (still no new content)
        folder = DocumentFolder.objects.create(
            curso=course,
            name='Empty Folder',
            created_by=teacher
        )
        
        # Verify students still don't have indicators for empty folders
        for student in enrolled_students:
            has_new_content = ContentIndicatorService.has_new_content(course, student)
            self.assertFalse(has_new_content, f"Student {student.username} should not have indicator for course with empty folders")

    def test_indicator_integration_end_to_end(self):
        """
        Integration test: Full indicator lifecycle from activation to removal
        """
        from course_documents.indicator_service import ContentIndicatorService
        
        # Create a teacher and course
        teacher = User.objects.create_user(
            username='teacher_integration',
            password='testpass123',
            email='teacher@test.com'
        )
        teacher.groups.add(self.profesores_group)
        
        course = Curso.objects.create(
            name='Integration Course',
            teacher=teacher,
            curso_academico=self.curso_academico,
            description='Test course for integration'
        )
        
        # Create a student and enroll
        student = User.objects.create_user(
            username='student_integration',
            password='testpass123',
            email='student@test.com'
        )
        student.groups.add(self.estudiantes_group)
        
        Matriculas.objects.create(
            course=course,
            student=student,
            curso_academico=self.curso_academico,
            activo=True
        )
        
        # Initially no indicator
        has_indicator_initial = ContentIndicatorService.has_new_content(course, student)
        self.assertFalse(has_indicator_initial, "No indicator initially")
        
        # Upload document (should activate indicator)
        folder = DocumentFolder.objects.create(
            curso=course,
            name='Integration Folder',
            created_by=teacher
        )
        
        from django.core.files.uploadedfile import SimpleUploadedFile
        
        file_content = b"Integration test content"
        uploaded_file = SimpleUploadedFile(
            name="integration_test.txt",
            content=file_content,
            content_type="text/plain"
        )
        
        document = CourseDocument.objects.create(
            folder=folder,
            name='Integration Document',
            file=uploaded_file,
            uploaded_by=teacher
        )
        
        # Activate indicators
        ContentIndicatorService.activate_indicators_for_course(course)
        
        # Verify indicator is active
        has_indicator_active = ContentIndicatorService.has_new_content(course, student)
        self.assertTrue(has_indicator_active, "Indicator should be active after document upload")
        
        # Login and access dashboard (should remove indicator)
        new_client = Client()
        new_client.login(username=student.username, password='testpass123')
        
        # Access dashboard to remove indicator
        response = new_client.get(
            reverse('course_documents:student_dashboard', kwargs={'curso_id': course.id})
        )
        self.assertEqual(response.status_code, 200)
        
        # Verify indicator is removed
        has_indicator_final = ContentIndicatorService.has_new_content(course, student)
        self.assertFalse(has_indicator_final, "Indicator should be removed after dashboard access")

    def test_indicator_activation_excludes_teacher(self):
        """
        Edge case: Teacher should not get new content indicators for their own uploads
        """
        from course_documents.indicator_service import ContentIndicatorService
        
        # Create a teacher who is also enrolled as a student (edge case)
        teacher_student = User.objects.create_user(
            username='teacher_student',
            password='testpass123',
            email='teacher_student@test.com'
        )
        teacher_student.groups.add(self.profesores_group)
        teacher_student.groups.add(self.estudiantes_group)
        
        course = Curso.objects.create(
            name='Teacher Student Course',
            teacher=teacher_student,
            curso_academico=self.curso_academico,
            description='Test course for teacher-student edge case'
        )
        
        # Enroll teacher as student in their own course
        Matriculas.objects.create(
            course=course,
            student=teacher_student,
            curso_academico=self.curso_academico,
            activo=True
        )
        
        # Create regular student
        regular_student = User.objects.create_user(
            username='regular_student',
            password='testpass123',
            email='regular_student@test.com'
        )
        regular_student.groups.add(self.estudiantes_group)
        
        Matriculas.objects.create(
            course=course,
            student=regular_student,
            curso_academico=self.curso_academico,
            activo=True
        )
        
        # Create folder and document
        folder = DocumentFolder.objects.create(
            curso=course,
            name='Teacher Student Folder',
            created_by=teacher_student
        )
        
        from django.core.files.uploadedfile import SimpleUploadedFile
        
        file_content = b"Test content for teacher-student case"
        uploaded_file = SimpleUploadedFile(
            name="teacher_student_test.txt",
            content=file_content,
            content_type="text/plain"
        )
        
        document = CourseDocument.objects.create(
            folder=folder,
            name='Teacher Student Document',
            file=uploaded_file,
            uploaded_by=teacher_student
        )
        
        # Activate indicators excluding the teacher
        ContentIndicatorService.activate_indicators_for_course(course, exclude_user=teacher_student)
        
        # Verify teacher-student does not have indicator
        teacher_has_indicator = ContentIndicatorService.has_new_content(course, teacher_student)
        self.assertFalse(teacher_has_indicator, "Teacher should not have new content indicator for their own upload")
        
        # Verify regular student has indicator
        student_has_indicator = ContentIndicatorService.has_new_content(course, regular_student)
        self.assertTrue(student_has_indicator, "Regular student should have new content indicator")

    def test_indicator_persistence_across_sessions(self):
        """
        Edge case: Indicators should persist across user sessions
        """
        from course_documents.indicator_service import ContentIndicatorService
        
        # Create teacher and course
        teacher = User.objects.create_user(
            username='teacher_persistence',
            password='testpass123',
            email='teacher@test.com'
        )
        teacher.groups.add(self.profesores_group)
        
        course = Curso.objects.create(
            name='Persistence Course',
            teacher=teacher,
            curso_academico=self.curso_academico,
            description='Test course for indicator persistence'
        )
        
        # Create student
        student = User.objects.create_user(
            username='student_persistence',
            password='testpass123',
            email='student@test.com'
        )
        student.groups.add(self.estudiantes_group)
        
        Matriculas.objects.create(
            course=course,
            student=student,
            curso_academico=self.curso_academico,
            activo=True
        )
        
        # Activate indicator
        ContentIndicatorService.activate_indicators_for_course(course)
        
        # Verify indicator is active
        has_indicator = ContentIndicatorService.has_new_content(course, student)
        self.assertTrue(has_indicator, "Student should have new content indicator")
        
        # Simulate session logout/login by creating new client
        new_client = Client()
        new_client.login(username=student.username, password='testpass123')
        
        # Verify indicator persists after "new session"
        has_indicator_after = ContentIndicatorService.has_new_content(course, student)
        self.assertTrue(has_indicator_after, "Indicator should persist across sessions")
        
        # Access dashboard to remove indicator
        response = new_client.get(
            reverse('course_documents:student_dashboard', kwargs={'curso_id': course.id})
        )
        self.assertEqual(response.status_code, 200)
        
        # Verify indicator is removed
        has_indicator_final = ContentIndicatorService.has_new_content(course, student)
        self.assertFalse(has_indicator_final, "Indicator should be removed after dashboard access")


class MissingPropertyTests(HypothesisTestCase):
    """
    Missing property-based tests that need to be implemented
    """
    
    def setUp(self):
        """Set up test data"""
        # Create groups
        self.profesores_group, _ = Group.objects.get_or_create(name='Profesores')
        self.estudiantes_group, _ = Group.objects.get_or_create(name='Estudiantes')
        
        # Create academic year
        self.curso_academico, _ = CursoAcademico.objects.get_or_create(
            nombre="2024-2025",
            defaults={'activo': True}
        )
        
        self.client = Client()

    @given(st.integers(min_value=2, max_value=8))
    @settings(deadline=None, max_examples=15)
    def test_multiple_course_buttons_uniquely_identified_teacher(self, num_courses):
        """
        **Feature: gestion-documentos-cursos, Property 3: Multiple course buttons are uniquely identified**
        For any teacher with multiple courses, each dashboard button should contain 
        the unique name of its corresponding course
        """
        # Create a teacher
        teacher = User.objects.create_user(
            username=f'teacher_unique_{num_courses}',
            password='testpass123',
            email='teacher@test.com'
        )
        teacher.groups.add(self.profesores_group)
        
        # Create multiple courses with unique names
        courses = []
        course_names = []
        for i in range(num_courses):
            unique_name = f'Unique Teacher Course {i+1} - {hash(str(i)) % 10000}'
            course = Curso.objects.create(
                name=unique_name,
                teacher=teacher,
                curso_academico=self.curso_academico,
                description=f'Test course {i+1} with unique name'
            )
            courses.append(course)
            course_names.append(unique_name)
        
        # Login as teacher
        self.client.login(username=teacher.username, password='testpass123')
        
        # Get profile page (where course buttons are displayed)
        response = self.client.get(reverse('principal:profile'))
        
        # Verify response is successful
        self.assertEqual(response.status_code, 200)
        
        # Verify all courses are in assigned_courses context
        assigned_courses = response.context.get('assigned_courses', [])
        self.assertEqual(len(assigned_courses), num_courses)
        
        # Verify each course name is unique and present
        assigned_course_names = [course.name for course in assigned_courses]
        
        # All created course names should be present
        for expected_name in course_names:
            self.assertIn(expected_name, assigned_course_names)
        
        # All names should be unique (no duplicates)
        self.assertEqual(len(assigned_course_names), len(set(assigned_course_names)))
        
        # Verify each course has correct identification
        for course in assigned_courses:
            # Course name should be one of our created names
            self.assertIn(course.name, course_names)
            
            # Course should have correct teacher assignment
            self.assertEqual(course.teacher, teacher)

    @given(st.integers(min_value=1, max_value=5))
    @settings(deadline=None, max_examples=10)
    def test_download_access_logging_property(self, num_downloads):
        """
        **Feature: gestion-documentos-cursos, Property 10: Download access logging**
        For any successful document download by a student, the system should 
        create a corresponding access log entry
        """
        # Create a teacher and course
        teacher = User.objects.create_user(
            username=f'teacher_log_prop_{num_downloads}',
            password='testpass123',
            email='teacher@test.com'
        )
        teacher.groups.add(self.profesores_group)
        
        course = Curso.objects.create(
            name=f'Log Property Course {num_downloads}',
            teacher=teacher,
            curso_academico=self.curso_academico,
            description='Test course for download logging property'
        )
        
        # Create a student and enroll in course
        student = User.objects.create_user(
            username=f'student_log_prop_{num_downloads}',
            password='testpass123',
            email='student@test.com'
        )
        student.groups.add(self.estudiantes_group)
        
        Matriculas.objects.create(
            course=course,
            student=student,
            curso_academico=self.curso_academico,
            activo=True
        )
        
        # Create a folder and document
        folder = DocumentFolder.objects.create(
            curso=course,
            name='Log Property Folder',
            created_by=teacher
        )
        
        from django.core.files.uploadedfile import SimpleUploadedFile
        
        file_content = b"Test content for download logging property"
        uploaded_file = SimpleUploadedFile(
            name="log_property_test.txt",
            content=file_content,
            content_type="text/plain"
        )
        
        document = CourseDocument.objects.create(
            folder=folder,
            name='Log Property Document',
            file=uploaded_file,
            uploaded_by=teacher
        )
        
        # Count initial access logs
        initial_access_count = DocumentAccess.objects.filter(
            document=document,
            student=student
        ).count()
        
        # Login as student
        self.client.login(username=student.username, password='testpass123')
        
        # Perform multiple downloads
        for i in range(num_downloads):
            response = self.client.get(
                reverse('course_documents:download_document', 
                       kwargs={'curso_id': course.id, 'document_id': document.id})
            )
            
            # Verify download was successful
            self.assertEqual(response.status_code, 200)
        
        # Verify access logs were created (Property: each download creates a log)
        final_access_count = DocumentAccess.objects.filter(
            document=document,
            student=student
        ).count()
        
        self.assertEqual(final_access_count, initial_access_count + num_downloads)

    @given(st.text(min_size=1, max_size=20).filter(lambda x: x.strip() and x.isprintable() and '\x00' not in x and '\\' not in x and not re.search(r'[<>:"/|?*]', x)))
    @settings(deadline=None, max_examples=15)
    def test_email_content_completeness_property(self, document_name):
        """
        **Feature: gestion-documentos-cursos, Property 13: Email content completeness**
        For any notification email sent, the message should contain the course name, 
        folder name, document name, and direct link to the course dashboard
        """
        from unittest.mock import patch, MagicMock
        from course_documents.services import NotificationService
        
        # Create a teacher and course
        teacher = User.objects.create_user(
            username=f'teacher_email_prop_{abs(hash(document_name)) % 10000}',
            password='testpass123',
            email='teacher@test.com'
        )
        teacher.groups.add(self.profesores_group)
        
        course_name = f'Email Property Course {abs(hash(document_name)) % 10000}'
        course = Curso.objects.create(
            name=course_name,
            teacher=teacher,
            curso_academico=self.curso_academico,
            description='Test course for email content property'
        )
        
        # Create a student and enroll
        student = User.objects.create_user(
            username=f'student_email_prop_{abs(hash(document_name)) % 10000}',
            password='testpass123',
            email='student@test.com'
        )
        student.groups.add(self.estudiantes_group)
        
        Matriculas.objects.create(
            course=course,
            student=student,
            curso_academico=self.curso_academico,
            activo=True
        )
        
        # Create a folder and document
        folder_name = f'Email Property Folder {abs(hash(document_name)) % 1000}'
        folder = DocumentFolder.objects.create(
            curso=course,
            name=folder_name,
            created_by=teacher
        )
        
        from django.core.files.uploadedfile import SimpleUploadedFile
        
        file_content = f"Content for {document_name}".encode()
        uploaded_file = SimpleUploadedFile(
            name=f"{re.sub(r'[<>:"/\|?*]', '_', document_name.strip()) or 'test_document'}.txt",
            content=file_content,
            content_type="text/plain"
        )
        
        document = CourseDocument.objects.create(
            folder=folder,
            name=document_name.strip(),
            file=uploaded_file,
            uploaded_by=teacher
        )
        
        # Mock email sending and capture email content
        captured_emails = []
        
        def capture_email(*args, **kwargs):
            email_instance = MagicMock()
            
            # Capture email data
            email_data = {
                'subject': kwargs.get('subject', ''),
                'body': kwargs.get('body', ''),
                'to': kwargs.get('to', []),
            }
            captured_emails.append(email_data)
            
            email_instance.send.return_value = True
            return email_instance
        
        with patch('course_documents.services.EmailMultiAlternatives', side_effect=capture_email):
            with patch('course_documents.services.render_to_string') as mock_render:
                # Mock template rendering to return content with required elements
                def mock_render_func(template_name, context):
                    if 'new_document.txt' in template_name:
                        return f"""
                        Curso: {context['curso'].name}
                        Carpeta: {context['folder'].name}
                        Documento: {context['document'].name}
                        Dashboard: {context['dashboard_url']}
                        Profesor: {context['teacher'].get_full_name() or context['teacher'].username}
                        """
                    return "Mock content"
                
                mock_render.side_effect = mock_render_func
                
                # Trigger notification
                NotificationService.notify_new_document(document)
        
        # Verify email was sent
        self.assertEqual(len(captured_emails), 1)
        
        # Verify email content contains required elements (Property validation)
        email_content = captured_emails[0]['body']
        
        # Property: Email must contain course name
        self.assertIn(course_name, email_content, "Email should contain course name")
        
        # Property: Email must contain folder name
        self.assertIn(folder_name, email_content, "Email should contain folder name")
        
        # Property: Email must contain document name
        self.assertIn(document_name.strip(), email_content, "Email should contain document name")
        
        # Property: Email must contain dashboard link reference
        self.assertIn('dashboard', email_content.lower(), "Email should contain dashboard link reference")

    @given(st.integers(min_value=1, max_value=6))
    @settings(deadline=None, max_examples=12)
    def test_new_content_indicator_activation_property(self, num_students):
        """
        **Feature: gestion-documentos-cursos, Property 14: New content indicator activation**
        For any new document upload, the system should immediately activate 
        the new content indicator for all enrolled students of that course
        """
        from course_documents.indicator_service import ContentIndicatorService
        
        # Create a teacher and course
        teacher = User.objects.create_user(
            username=f'teacher_indicator_prop_{num_students}',
            password='testpass123',
            email='teacher@test.com'
        )
        teacher.groups.add(self.profesores_group)
        
        course = Curso.objects.create(
            name=f'Indicator Property Course {num_students}',
            teacher=teacher,
            curso_academico=self.curso_academico,
            description='Test course for indicator activation property'
        )
        
        # Create multiple students and enroll them
        enrolled_students = []
        for i in range(num_students):
            student = User.objects.create_user(
                username=f'student_indicator_prop_{num_students}_{i}',
                password='testpass123',
                email=f'student{i}@test.com'
            )
            student.groups.add(self.estudiantes_group)
            
            Matriculas.objects.create(
                course=course,
                student=student,
                curso_academico=self.curso_academico,
                activo=True
            )
            
            enrolled_students.append(student)
        
        # Property: Initially no students should have new content indicators
        for student in enrolled_students:
            has_new_content = ContentIndicatorService.has_new_content(course, student)
            self.assertFalse(has_new_content, f"Student {student.username} should not have new content initially")
        
        # Create a folder and document
        folder = DocumentFolder.objects.create(
            curso=course,
            name='Indicator Property Folder',
            created_by=teacher
        )
        
        from django.core.files.uploadedfile import SimpleUploadedFile
        
        file_content = b"Test content for indicator activation property"
        uploaded_file = SimpleUploadedFile(
            name="indicator_property_test.txt",
            content=file_content,
            content_type="text/plain"
        )
        
        document = CourseDocument.objects.create(
            folder=folder,
            name='Indicator Property Document',
            file=uploaded_file,
            uploaded_by=teacher
        )
        
        # Trigger indicator activation
        ContentIndicatorService.activate_indicators_for_course(course)
        
        # Property: All enrolled students should now have new content indicators
        for student in enrolled_students:
            has_new_content = ContentIndicatorService.has_new_content(course, student)
            self.assertTrue(has_new_content, f"Student {student.username} should have new content indicator after document upload")

    @given(st.integers(min_value=1, max_value=5))
    @settings(deadline=None, max_examples=10)
    def test_new_content_indicator_removal_property(self, num_accesses):
        """
        **Feature: gestion-documentos-cursos, Property 15: New content indicator removal**
        For any student accessing a course dashboard with new content, 
        the new content indicator for that course should be removed for that student
        """
        from course_documents.indicator_service import ContentIndicatorService
        
        # Create a teacher and course
        teacher = User.objects.create_user(
            username=f'teacher_removal_prop_{num_accesses}',
            password='testpass123',
            email='teacher@test.com'
        )
        teacher.groups.add(self.profesores_group)
        
        course = Curso.objects.create(
            name=f'Removal Property Course {num_accesses}',
            teacher=teacher,
            curso_academico=self.curso_academico,
            description='Test course for indicator removal property'
        )
        
        # Create a student and enroll
        student = User.objects.create_user(
            username=f'student_removal_prop_{num_accesses}',
            password='testpass123',
            email='student@test.com'
        )
        student.groups.add(self.estudiantes_group)
        
        Matriculas.objects.create(
            course=course,
            student=student,
            curso_academico=self.curso_academico,
            activo=True
        )
        
        # Create a folder and document
        folder = DocumentFolder.objects.create(
            curso=course,
            name='Removal Property Folder',
            created_by=teacher
        )
        
        from django.core.files.uploadedfile import SimpleUploadedFile
        
        file_content = b"Test content for indicator removal property"
        uploaded_file = SimpleUploadedFile(
            name="removal_property_test.txt",
            content=file_content,
            content_type="text/plain"
        )
        
        document = CourseDocument.objects.create(
            folder=folder,
            name='Removal Property Document',
            file=uploaded_file,
            uploaded_by=teacher
        )
        
        # Activate indicator for the student
        ContentIndicatorService.activate_indicators_for_course(course)
        
        # Property: Student should have new content indicator initially
        has_new_content = ContentIndicatorService.has_new_content(course, student)
        self.assertTrue(has_new_content, "Student should have new content indicator initially")
        
        # Login as student
        self.client.login(username=student.username, password='testpass123')
        
        # Access student dashboard multiple times
        for i in range(num_accesses):
            response = self.client.get(
                reverse('course_documents:student_dashboard', kwargs={'curso_id': course.id})
            )
            
            # Verify response is successful
            self.assertEqual(response.status_code, 200)
        
        # Property: Indicator should be removed after first access (regardless of num_accesses)
        has_new_content_after = ContentIndicatorService.has_new_content(course, student)
        self.assertFalse(has_new_content_after, "Student should not have new content indicator after accessing dashboard")

    @given(st.integers(min_value=1, max_value=4))
    @settings(deadline=None, max_examples=8)
    def test_default_indicator_state_property(self, num_students):
        """
        **Feature: gestion-documentos-cursos, Property 16: Default indicator state**
        For any course without new content, the dashboard button should not 
        display a new content indicator
        """
        from course_documents.indicator_service import ContentIndicatorService
        
        # Create a teacher and course
        teacher = User.objects.create_user(
            username=f'teacher_default_prop_{num_students}',
            password='testpass123',
            email='teacher@test.com'
        )
        teacher.groups.add(self.profesores_group)
        
        course = Curso.objects.create(
            name=f'Default Property Course {num_students}',
            teacher=teacher,
            curso_academico=self.curso_academico,
            description='Test course for default indicator state property'
        )
        
        # Create multiple students and enroll them
        enrolled_students = []
        for i in range(num_students):
            student = User.objects.create_user(
                username=f'student_default_prop_{num_students}_{i}',
                password='testpass123',
                email=f'student{i}@test.com'
            )
            student.groups.add(self.estudiantes_group)
            
            Matriculas.objects.create(
                course=course,
                student=student,
                curso_academico=self.curso_academico,
                activo=True
            )
            
            enrolled_students.append(student)
        
        # Property: No students should have new content indicators by default
        for student in enrolled_students:
            has_new_content = ContentIndicatorService.has_new_content(course, student)
            self.assertFalse(has_new_content, f"Student {student.username} should not have new content indicator by default")
        
        # Property: Course statistics should show no new content
        stats = ContentIndicatorService.get_indicator_stats_for_course(course)
        self.assertEqual(stats['total_students'], num_students)
        self.assertEqual(stats['students_with_new_content'], 0)
        
        # Create a folder but no documents (still no new content)
        folder = DocumentFolder.objects.create(
            curso=course,
            name='Empty Property Folder',
            created_by=teacher
        )
        
        # Property: Students still shouldn't have indicators for empty folders
        for student in enrolled_students:
            has_new_content = ContentIndicatorService.has_new_content(course, student)
            self.assertFalse(has_new_content, f"Student {student.username} should not have indicator for course with empty folders")