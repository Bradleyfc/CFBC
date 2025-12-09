from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import UsuarioArchivado

class ReclamarUsuarioArchivadoForm(forms.Form):
    """
    Formulario para que usuarios reclamen su cuenta archivada
    """
    username = forms.CharField(
        max_length=150,
        label='Nombre de usuario',
        help_text='Ingrese su nombre de usuario anterior'
    )
    email = forms.EmailField(
        label='Correo electrónico',
        help_text='Ingrese el correo asociado a su cuenta anterior'
    )
    carnet = forms.CharField(
        max_length=11,
        required=False,
        label='Carnet de identidad',
        help_text='Ingrese su carnet para verificar identidad (opcional)'
    )
    nueva_password = forms.CharField(
        widget=forms.PasswordInput,
        label='Nueva contraseña',
        min_length=8
    )
    confirmar_password = forms.CharField(
        widget=forms.PasswordInput,
        label='Confirmar contraseña'
    )
    
    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        email = cleaned_data.get('email')
        carnet = cleaned_data.get('carnet')
        nueva_password = cleaned_data.get('nueva_password')
        confirmar_password = cleaned_data.get('confirmar_password')
        
        # Verificar que las contraseñas coincidan
        if nueva_password and confirmar_password:
            if nueva_password != confirmar_password:
                raise forms.ValidationError('Las contraseñas no coinciden')
        
        # Verificar que el usuario archivado existe
        if username and email:
            usuario_encontrado = None
            tipo_fuente = None
            
            # Primero buscar en UsuarioArchivado
            try:
                usuario_archivado = UsuarioArchivado.objects.get(
                    username=username,
                    email=email
                )
                
                # Verificar carnet si se proporciona
                if carnet and usuario_archivado.carnet:
                    if usuario_archivado.carnet != carnet:
                        raise forms.ValidationError('Los datos no coinciden con los registros')
                
                # Verificar que no tenga ya un usuario actual
                if usuario_archivado.usuario_actual:
                    raise forms.ValidationError(
                        'Esta cuenta ya ha sido reclamada. Intente recuperar su contraseña.'
                    )
                
                usuario_encontrado = usuario_archivado
                tipo_fuente = 'usuario_archivado'
                
            except UsuarioArchivado.DoesNotExist:
                # Si no está en UsuarioArchivado, buscar en DatoArchivadoDinamico
                from .models import DatoArchivadoDinamico
                from django.db.models import Q
                
                try:
                    # Buscar en datos archivados dinámicos - tabla auth_user
                    dato_archivado = DatoArchivadoDinamico.objects.filter(
                        tabla_origen='auth_user'
                    ).filter(
                        Q(datos_originales__username=username) &
                        Q(datos_originales__email__iexact=email)
                    ).first()
                    
                    if dato_archivado:
                        usuario_encontrado = dato_archivado
                        tipo_fuente = 'dato_dinamico'
                    else:
                        raise forms.ValidationError(
                            'No se encontró un usuario archivado con esos datos. '
                            'Verifique que el nombre de usuario y email sean correctos.'
                        )
                        
                except Exception as e:
                    raise forms.ValidationError(
                        'No se encontró un usuario archivado con esos datos. '
                        'Verifique que el nombre de usuario y email sean correctos.'
                    )
            
            if usuario_encontrado:
                cleaned_data['usuario_encontrado'] = usuario_encontrado
                cleaned_data['tipo_fuente'] = tipo_fuente
        
        return cleaned_data
    
    def save(self):
        """
        Crea el usuario actual basado en los datos archivados
        """
        usuario_archivado = self.cleaned_data['usuario_archivado']
        nueva_password = self.cleaned_data['nueva_password']
        
        # Crear usuario actual
        user = User.objects.create_user(
            username=usuario_archivado.username,
            email=usuario_archivado.email,
            first_name=usuario_archivado.first_name,
            last_name=usuario_archivado.last_name,
            password=nueva_password,
            is_active=True
        )
        
        # Asignar siempre al grupo Estudiantes
        try:
            from django.contrib.auth.models import Group
            grupo_estudiantes = Group.objects.get(name='Estudiantes')
            user.groups.add(grupo_estudiantes)
        except Group.DoesNotExist:
            # Crear el grupo si no existe
            grupo_estudiantes = Group.objects.create(name='Estudiantes')
            user.groups.add(grupo_estudiantes)
        
        # Vincular usuario archivado con usuario actual
        usuario_archivado.usuario_actual = user
        usuario_archivado.save()
        
        return user

class BuscarUsuarioArchivadoForm(forms.Form):
    """
    Formulario para buscar usuarios archivados por correo electrónico
    """
    busqueda = forms.EmailField(
        max_length=200,
        label='Correo electrónico',
        help_text='Ingrese su correo electrónico para buscar su cuenta archivada',
        widget=forms.EmailInput(attrs={
            'placeholder': 'Ej: juan.perez@email.com',
            'class': 'form-control'
        })
    )
    
    def buscar_usuarios(self):
        """
        Busca usuarios archivados por correo electrónico en todas las tablas archivadas disponibles
        """
        email_busqueda = self.cleaned_data.get('busqueda', '').strip()
        
        if not email_busqueda:
            return []
        
        from django.db.models import Q
        from .models import DatoArchivadoDinamico
        
        usuarios_encontrados = []
        
        # Primero buscar en UsuarioArchivado (si hay datos)
        try:
            usuarios_archivados = UsuarioArchivado.objects.filter(
                email__iexact=email_busqueda
            ).filter(usuario_actual__isnull=True)  # Solo no reclamados
            
            for usuario in usuarios_archivados:
                usuarios_encontrados.append({
                    'tipo': 'usuario_archivado',
                    'id': usuario.id,
                    'username': usuario.username,
                    'first_name': usuario.first_name,
                    'last_name': usuario.last_name,
                    'email': usuario.email,
                    'carnet': usuario.carnet,
                    'grupo': usuario.grupo,
                    'date_joined': usuario.date_joined,
                    'fuente': 'Usuarios Archivados'
                })
        except Exception:
            pass
        
        # Buscar en datos archivados dinámicos - tabla auth_user
        try:
            datos_auth_user = DatoArchivadoDinamico.objects.filter(
                tabla_origen='auth_user'
            ).filter(
                datos_originales__email__iexact=email_busqueda
            )
            
            for dato in datos_auth_user:
                datos = dato.datos_originales
                usuarios_encontrados.append({
                    'tipo': 'dato_dinamico',
                    'id': dato.id,
                    'username': datos.get('username', ''),
                    'first_name': datos.get('first_name', ''),
                    'last_name': datos.get('last_name', ''),
                    'email': datos.get('email', ''),
                    'carnet': None,
                    'grupo': None,
                    'date_joined': datos.get('date_joined'),
                    'fuente': 'Tabla auth_user archivada',
                    'id_original': dato.id_original
                })
        except Exception:
            pass
        
        # Buscar en otras tablas que puedan contener información de usuarios
        try:
            # Buscar en tablas de perfiles o usuarios por email
            tablas_usuario = ['auth_user', 'usuarios', 'profiles', 'user_profile', 'perfil_usuario']
            
            for tabla in tablas_usuario:
                datos_tabla = DatoArchivadoDinamico.objects.filter(
                    tabla_origen=tabla
                ).filter(
                    Q(datos_originales__email__iexact=email_busqueda) |
                    Q(datos_originales__correo__iexact=email_busqueda)
                )
                
                for dato in datos_tabla:
                    datos = dato.datos_originales
                    # Intentar extraer información de usuario
                    username = datos.get('username') or datos.get('user') or datos.get('nombre_usuario')
                    email = datos.get('email') or datos.get('correo')
                    first_name = datos.get('first_name') or datos.get('nombre') or datos.get('name')
                    last_name = datos.get('last_name') or datos.get('apellido') or datos.get('apellidos')
                    
                    # Solo agregar si tiene email y coincide con la búsqueda
                    if email and email.lower() == email_busqueda.lower():
                        usuarios_encontrados.append({
                            'tipo': 'dato_dinamico',
                            'id': dato.id,
                            'username': username or 'N/A',
                            'first_name': first_name or '',
                            'last_name': last_name or '',
                            'email': email or '',
                            'carnet': datos.get('carnet') or datos.get('ci') or datos.get('cedula'),
                            'grupo': datos.get('grupo') or datos.get('role') or datos.get('tipo_usuario'),
                            'date_joined': datos.get('date_joined') or datos.get('fecha_registro') or datos.get('created_at'),
                            'fuente': f'Tabla {tabla} archivada',
                            'id_original': dato.id_original,
                            'datos_completos': datos
                        })
        except Exception:
            pass
        
        # Eliminar duplicados basados en email
        usuarios_unicos = {}
        for usuario in usuarios_encontrados:
            key = usuario['email'].lower() if usuario['email'] else f"sin_email_{usuario['id']}"
            if key not in usuarios_unicos:
                usuarios_unicos[key] = usuario
        
        return list(usuarios_unicos.values())[:20]  # Limitar a 20 resultados