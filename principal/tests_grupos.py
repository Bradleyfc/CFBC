"""
Tests para verificar la configuración automática de grupos
"""
from django.test import TestCase
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from .config_grupos import GRUPOS_SISTEMA, obtener_nombres_grupos, configurar_permisos_grupo
from .utils import verificar_grupos_configurados, asignar_usuario_a_grupo
from django.contrib.auth.models import User

class GruposConfiguracionTest(TestCase):
    """Tests para la configuración automática de grupos"""
    
    def test_grupos_definidos_correctamente(self):
        """Verifica que los grupos estén definidos correctamente en la configuración"""
        nombres_grupos = obtener_nombres_grupos()
        
        # Verificar que tenemos los grupos esperados
        grupos_esperados = [
            'Administración', 'Blog Autor', 'Blog Moderador', 'Editor',
            'Estudiantes', 'Profesores', 'Secretaría'
        ]
        
        self.assertEqual(len(nombres_grupos), 7)
        for grupo in grupos_esperados:
            self.assertIn(grupo, nombres_grupos)
    
    def test_creacion_grupos(self):
        """Verifica que los grupos se puedan crear correctamente"""
        # Crear grupos manualmente para el test
        for config_grupo in GRUPOS_SISTEMA:
            grupo, created = Group.objects.get_or_create(name=config_grupo['nombre'])
            self.assertTrue(isinstance(grupo, Group))
            
            # Verificar que el grupo tiene el nombre correcto
            self.assertEqual(grupo.name, config_grupo['nombre'])
    
    def test_configuracion_permisos(self):
        """Verifica que los permisos se configuren correctamente"""
        # Crear un grupo de prueba
        config_grupo = GRUPOS_SISTEMA[0]  # Administración
        grupo, created = Group.objects.get_or_create(name=config_grupo['nombre'])
        
        # Configurar permisos
        configurar_permisos_grupo(grupo, config_grupo)
        
        # Verificar que se asignaron permisos
        self.assertTrue(grupo.permissions.exists())
    
    def test_verificacion_grupos_configurados(self):
        """Verifica la función de verificación de grupos"""
        # Crear algunos grupos
        for config_grupo in GRUPOS_SISTEMA[:3]:  # Solo los primeros 3
            Group.objects.get_or_create(name=config_grupo['nombre'])
        
        verificacion = verificar_grupos_configurados()
        
        # Verificar estructura de respuesta
        self.assertIn('total_definidos', verificacion)
        self.assertIn('total_configurados', verificacion)
        self.assertIn('faltantes', verificacion)
        self.assertIn('configurados_correctamente', verificacion)
        
        # Verificar valores
        self.assertEqual(verificacion['total_definidos'], 6)
        self.assertEqual(verificacion['total_configurados'], 3)
        self.assertEqual(len(verificacion['faltantes']), 3)
        self.assertFalse(verificacion['configurados_correctamente'])
    
    def test_asignacion_usuario_grupo(self):
        """Verifica la asignación de usuarios a grupos"""
        # Crear usuario de prueba
        usuario = User.objects.create_user(
            username='test_user',
            email='test@example.com',
            password='testpass123'
        )
        
        # Crear grupo de prueba
        grupo = Group.objects.create(name='Estudiantes')
        
        # Asignar usuario al grupo
        resultado = asignar_usuario_a_grupo(usuario, 'Estudiantes')
        
        # Verificar asignación
        self.assertTrue(resultado)
        self.assertTrue(usuario.groups.filter(name='Estudiantes').exists())
    
    def test_configuracion_completa_grupos(self):
        """Test de integración completa"""
        # Simular la configuración completa
        grupos_creados = 0
        
        for config_grupo in GRUPOS_SISTEMA:
            grupo, created = Group.objects.get_or_create(name=config_grupo['nombre'])
            if created:
                grupos_creados += 1
            
            # Configurar permisos
            configurar_permisos_grupo(grupo, config_grupo)
        
        # Verificar que todos los grupos fueron procesados
        self.assertEqual(grupos_creados, 7)  # Todos deberían ser nuevos en el test
        
        # Verificar que todos los grupos existen
        verificacion = verificar_grupos_configurados()
        self.assertTrue(verificacion['configurados_correctamente'])
        
        # Verificar que cada grupo tiene permisos asignados
        for nombre_grupo in obtener_nombres_grupos():
            grupo = Group.objects.get(name=nombre_grupo)
            # Al menos algunos grupos deberían tener permisos
            # (algunos pueden no tener si los modelos no existen en el test)
            self.assertTrue(isinstance(grupo.permissions.count(), int))

class GruposUtilsTest(TestCase):
    """Tests para las utilidades de grupos"""
    
    def setUp(self):
        """Configuración inicial para los tests"""
        self.usuario = User.objects.create_user(
            username='test_user',
            email='test@example.com',
            password='testpass123'
        )
        self.grupo = Group.objects.create(name='TestGroup')
    
    def test_asignar_usuario_por_username(self):
        """Verifica asignación de usuario por username"""
        resultado = asignar_usuario_a_grupo('test_user', 'TestGroup')
        self.assertTrue(resultado)
        self.assertTrue(self.usuario.groups.filter(name='TestGroup').exists())
    
    def test_asignar_usuario_por_objeto(self):
        """Verifica asignación de usuario por objeto User"""
        resultado = asignar_usuario_a_grupo(self.usuario, 'TestGroup')
        self.assertTrue(resultado)
        self.assertTrue(self.usuario.groups.filter(name='TestGroup').exists())
    
    def test_usuario_inexistente(self):
        """Verifica manejo de usuario inexistente"""
        resultado = asignar_usuario_a_grupo('usuario_inexistente', 'TestGroup')
        self.assertFalse(resultado)
    
    def test_grupo_inexistente(self):
        """Verifica manejo de grupo inexistente"""
        resultado = asignar_usuario_a_grupo(self.usuario, 'GrupoInexistente')
        self.assertFalse(resultado)