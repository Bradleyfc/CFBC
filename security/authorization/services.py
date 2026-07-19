"""
Authorization Service (AZ) implementation.

Implements:
- Role-Based Access Control (RBAC) with hierarchical roles
- Object-level permissions (CRUD on individual resources)
- Time-based access policies
- Row-Level Security (RLS) integration
- Authorization logging
"""

import logging
from datetime import datetime
from typing import List, Optional, Type, Union

from django.conf import settings
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models import Model, QuerySet
from django.utils import timezone

from django.db import connection

from security.models import (
    Role, UserRoleAssignment, ObjectPermission, TimeBasedAccessPolicy,
    AuthorizationAuditLog, RowLevelSecurityPolicy,
)

logger = logging.getLogger(__name__)


class RBACService:
    """
    Servicio de control de acceso basado en roles jerárquicos.

    Soporta hasta 3 niveles de herencia:
    superuser > admin > editor > viewer
    """

    @staticmethod
    def create_role(
        name: str,
        permissions: List[str] = None,
        parent: Optional[Role] = None,
        description: str = '',
        is_system_role: bool = False
    ) -> Role:
        """
        Crea un nuevo rol con permisos específicos.

        Args:
            name: Nombre del rol
            permissions: Lista de codenames de permisos
            parent: Rol padre (hereda sus permisos)
            description: Descripción del rol
            is_system_role: Si es un rol del sistema

        Returns:
            Role: El rol creado
        """
        role, _ = Role.objects.get_or_create(
            name=name,
            defaults={
                'parent': parent,
                'description': description,
                'is_system_role': is_system_role,
            }
        )

        if permissions:
            for codename in permissions:
                try:
                    perm = Permission.objects.get(codename=codename)
                    role.permissions.add(perm)
                except Permission.DoesNotExist:
                    logger.warning(f'Permission not found: {codename}')

        return role

    @staticmethod
    def assign_role(
        user: User,
        role: Role,
        assigned_by: Optional[User] = None,
        expires_at: Optional[datetime] = None
    ):
        """
        Asigna un rol a un usuario.

        Args:
            user: Usuario
            role: Rol a asignar
            assigned_by: Usuario que asigna el rol
            expires_at: Fecha de expiración de la asignación
        """
        assignment, created = UserRoleAssignment.objects.get_or_create(
            user=user,
            role=role,
            defaults={
                'assigned_by': assigned_by,
                'expires_at': expires_at or (timezone.now() + timezone.timedelta(days=365)),
            }
        )

        if not created and not assignment.is_active:
            assignment.is_active = True
            assignment.save()

        logger.info(
            f'Role "{role.name}" assigned to user "{user.username}"'
        )

    @staticmethod
    def remove_role(user: User, role: Role):
        """
        Remueve un rol de un usuario.

        Args:
            user: Usuario
            role: Rol a remover
        """
        try:
            assignment = UserRoleAssignment.objects.get(
                user=user, role=role, is_active=True
            )
            assignment.is_active = False
            assignment.save()

            logger.info(
                f'Role "{role.name}" removed from user "{user.username}"'
            )
        except UserRoleAssignment.DoesNotExist:
            logger.warning(
                f'No active assignment found for role "{role.name}" '
                f'and user "{user.username}"'
            )

    @staticmethod
    def get_user_roles(user: User) -> List[Role]:
        """
        Obtiene todos los roles activos de un usuario.

        Args:
            user: Usuario

        Returns:
            List[Role]: Lista de roles activos
        """
        assignments = UserRoleAssignment.objects.filter(
            user=user, is_active=True
        ).select_related('role')

        # Filtrar expirados
        now = timezone.now()
        valid_assignments = [
            a for a in assignments
            if a.expires_at is None or a.expires_at > now
        ]

        return [a.role for a in valid_assignments]

    @staticmethod
    def get_user_permissions(user: User) -> set:
        """
        Obtiene todos los permisos de un usuario incluyendo herencia.

        Args:
            user: Usuario

        Returns:
            set: Conjunto de codenames de permisos
        """
        permissions = set()

        # Obtener permisos de roles
        roles = RBACService.get_user_roles(user)
        for role in roles:
            inherited_perms = role.get_inherited_permissions()
            permissions.update(p.codename for p in inherited_perms)

        # Obtener permisos de groups de Django
        for group in user.groups.all():
            permissions.update(
                p.codename for p in group.permissions.all()
            )

        # Obtener permisos individuales del usuario
        permissions.update(
                p.codename for p in user.user_permissions.all()
        )

        return permissions

    @staticmethod
    def check_permission(
        user: User,
        permission_codename: str,
        obj: Optional[Model] = None
    ) -> bool:
        """
        Verifica si un usuario tiene un permiso específico.

        Args:
            user: Usuario
            permission_codename: Codename del permiso
            obj: Objeto específico (para permisos por objeto)

        Returns:
            bool: True si el usuario tiene el permiso
        """
        # Superusers tienen todos los permisos
        if user.is_superuser:
            return True

        # Verificar permisos de roles y grupos
        user_permissions = RBACService.get_user_permissions(user)
        if permission_codename in user_permissions:
            return True

        # Verificar permiso por objeto si aplica
        if obj:
            try:
                ObjectPermission.objects.get(
                    user=user,
                    permission__codename=permission_codename,
                    content_type=ContentType.objects.get_for_model(obj),
                    object_id=obj.pk,
                )
                return True
            except ObjectPermission.DoesNotExist:
                pass

        return False

    @staticmethod
    def check_time_based_access(user: User, resource: str = None) -> bool:
        """
        Verifica si el usuario tiene acceso según políticas de tiempo.

        Args:
            user: Usuario
            resource: Recurso opcional

        Returns:
            bool: True si tiene acceso según horario
        """
        roles = RBACService.get_user_roles(user)
        now = timezone.now()
        current_hour = now.hour
        current_day = now.strftime('%A')

        for role in roles:
            policies = TimeBasedAccessPolicy.objects.filter(
                roles=role, is_active=True
            )
            for policy in policies:
                if current_day not in policy.allowed_days:
                    return False
                if not (policy.start_hour <= current_hour < policy.end_hour):
                    return False

        return True

    @staticmethod
    def get_objects_with_permission(
        user: User,
        model_class: Type[Model],
        permission_codename: str
    ) -> QuerySet:
        """
        Obtiene un QuerySet de objetos para los que el usuario tiene permiso.

        Args:
            user: Usuario
            model_class: Clase del modelo
            permission_codename: Codename del permiso

        Returns:
            QuerySet: Objetos a los que el usuario tiene acceso
        """
        # Superusers ven todo
        if user.is_superuser:
            return model_class.objects.all()

        # Obtener IDs de objetos con permisos directos
        content_type = ContentType.objects.get_for_model(model_class)
        permitted_ids = ObjectPermission.objects.filter(
            user=user,
            permission__codename=permission_codename,
            content_type=content_type,
        ).values_list('object_id', flat=True)

        return model_class.objects.filter(pk__in=permitted_ids)


class TimeBasedAccessService:
    """
    Servicio de políticas de acceso basadas en tiempo.
    """

    @staticmethod
    def create_policy(
        name: str,
        start_hour: int = 8,
        end_hour: int = 18,
        allowed_days: List[str] = None,
        timezone_str: str = 'UTC',
        roles: List[Role] = None,
    ) -> TimeBasedAccessPolicy:
        """
        Crea una política de acceso por tiempo.

        Args:
            name: Nombre de la política
            start_hour: Hora de inicio (0-23)
            end_hour: Hora de fin (0-23)
            allowed_days: Días permitidos
            timezone_str: Zona horaria
            roles: Roles a los que aplica

        Returns:
            TimeBasedAccessPolicy: La política creada
        """
        policy = TimeBasedAccessPolicy.objects.create(
            name=name,
            start_hour=start_hour,
            end_hour=end_hour,
            allowed_days=allowed_days or ['Monday', 'Tuesday', 'Wednesday',
                                          'Thursday', 'Friday'],
            timezone=timezone_str,
        )

        if roles:
            policy.roles.set(roles)

        return policy

    @staticmethod
    def is_access_allowed(user: User, policy: TimeBasedAccessPolicy) -> bool:
        """
        Verifica si un usuario tiene acceso según una política específica.

        Args:
            user: Usuario
            policy: Política de acceso por tiempo

        Returns:
            bool: True si el acceso está permitido
        """
        import pytz
        try:
            tz = pytz.timezone(policy.timezone)
        except pytz.UnknownTimeZoneError:
            tz = pytz.UTC

        now = timezone.now().astimezone(tz)
        current_hour = now.hour
        current_day = now.strftime('%A')

        if current_day not in policy.allowed_days:
            return False
        if not (policy.start_hour <= current_hour < policy.end_hour):
            return False

        return True


class ObjectPermissionService:
    """
    Servicio de permisos a nivel de objeto.
    """

    @staticmethod
    def assign_object_permission(
        user: User,
        permission_codename: str,
        obj: Model,
        granted_by: Optional[User] = None,
        expires_at: Optional[datetime] = None,
    ):
        """
        Asigna un permiso a nivel de objeto a un usuario.

        Args:
            user: Usuario
            permission_codename: Codename del permiso
            obj: Objeto
            granted_by: Usuario que otorga el permiso
            expires_at: Fecha de expiración
        """
        try:
            permission = Permission.objects.get(codename=permission_codename)
            content_type = ContentType.objects.get_for_model(obj)

            ObjectPermission.objects.update_or_create(
                user=user,
                permission=permission,
                content_type=content_type,
                object_id=obj.pk,
                defaults={
                    'granted_by': granted_by,
                    'expires_at': expires_at,
                }
            )
        except Permission.DoesNotExist:
            logger.error(f'Permission not found: {permission_codename}')

    @staticmethod
    def remove_object_permission(
        user: User,
        permission_codename: str,
        obj: Model,
    ):
        """
        Remueve un permiso a nivel de objeto.

        Args:
            user: Usuario
            permission_codename: Codename del permiso
            obj: Objeto
        """
        try:
            permission = Permission.objects.get(codename=permission_codename)
            content_type = ContentType.objects.get_for_model(obj)

            ObjectPermission.objects.filter(
                user=user,
                permission=permission,
                content_type=content_type,
                object_id=obj.pk,
            ).delete()
        except Permission.DoesNotExist:
            pass


class AuthorizationAuditService:
    """
    Servicio de auditoría de autorización.
    """

    @staticmethod
    def log_decision(
        user: User,
        resource_type: str,
        action: str,
        granted: bool,
        resource_id: str = None,
        reason: str = '',
        ip_address: str = None,
    ):
        """
        Registra una decisión de autorización para auditoría.

        Args:
            user: Usuario
            resource_type: Tipo de recurso
            action: Acción solicitada
            granted: Si fue concedida
            resource_id: ID del recurso
            reason: Razón de la decisión
            ip_address: Dirección IP
        """
        AuthorizationAuditLog.objects.create(
            user=user,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            outcome='granted' if granted else 'denied',
            reason=reason,
            ip_address=ip_address,
        )

        # También registrar en SecurityAuditLog para eventos importantes
        if not granted:
            from security.models import SecurityAuditLog
            SecurityAuditLog.objects.create(
                event_type=SecurityAuditLog.EventTypes.AUTHORIZATION,
                user=user,
                action=f'access_denied_{action}',
                resource=resource_type,
                resource_id=resource_id,
                details={
                    'action': action,
                    'reason': reason or 'access_denied',
                },
                success=False,
                severity=SecurityAuditLog.SeverityLevels.WARNING,
            )


class RowLevelSecurityService:
    """
    Servicio de seguridad a nivel de fila (RLS) para PostgreSQL.

    Integra con las políticas RLS a nivel de base de datos definidas
    en la migración 0002_enable_pgcrypto_rls.py.

    Las políticas RLS usan las funciones:
    - rls_set_context(user_id, user_role): Establece el contexto de RLS
    - rls_current_user_id(): Obtiene el ID del usuario actual
    - rls_current_user_role(): Obtiene el rol del usuario actual
    """

    @staticmethod
    def set_rls_context(user, role_name: str = None):
        """
        Establece el contexto RLS para la conexión actual de base de datos.

        Debe llamarse al inicio de cada request autenticado.
        Si no se llama, las políticas RLS denegarán el acceso por defecto.

        Args:
            user: Usuario (puede ser None para usuarios anónimos)
            role_name: Nombre del rol (si es None, se determina automáticamente)
        """
        if user is None or not user.is_authenticated:
            RowLevelSecurityService._set_rls_params(0, 'anonymous')
            return

        if role_name is None:
            # Determinar el rol del usuario (siempre en minúsculas para RLS)
            if user.is_superuser:
                role_name = 'superuser'
            else:
                roles = RBACService.get_user_roles(user)
                if roles:
                    # Usar el rol de mayor jerarquía, normalizado a minúsculas
                    role_name = roles[0].name.lower()
                else:
                    # Mapeo de grupos de Django a roles RLS
                    group_role_map = {
                        'administradores': 'admin',
                        'admin': 'admin',
                        'profesores': 'teacher',
                        'docentes': 'teacher',
                        'teacher': 'teacher',
                        'editores': 'editor',
                        'editor': 'editor',
                        'estudiantes': 'student',
                        'student': 'student',
                    }
                    user_group_names = [
                        g.name.lower() for g in user.groups.all()
                    ]
                    role_name = 'authenticated'
                    for group_name, mapped_role in group_role_map.items():
                        if group_name in user_group_names:
                            role_name = mapped_role
                            break

        RowLevelSecurityService._set_rls_params(user.id, role_name)

    @staticmethod
    def _set_rls_params(user_id: int, role_name: str):
        """
        Establece los parámetros de configuración de RLS en la sesión de BD.

        Args:
            user_id: ID del usuario (0 para anónimo)
            role_name: Nombre del rol
        """
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT rls_set_context(%s, %s);",
                    [user_id, role_name]
                )
        except Exception as e:
            logger.error(
                f"Error setting RLS context (user_id={user_id}, role={role_name}): {e}"
            )
            # Cerrar conexión para evitar estado inconsistente
            try:
                connection.close_if_unusable_or_healthy()
            except Exception:
                pass

    @staticmethod
    def clear_rls_context():
        """
        Limpia el contexto RLS (para usuarios anónimos).
        """
        RowLevelSecurityService._set_rls_params(0, 'anonymous')

    @staticmethod
    def create_selective_permission_policy(
        table_name: str,
        policy_name: str,
        using_expression: str,
        roles: List[str] = None,
    ) -> RowLevelSecurityPolicy:
        """
        Crea una política RLS para SELECT.

        Args:
            table_name: Nombre de la tabla
            policy_name: Nombre de la política
            using_expression: Expresión SQL para USING clause
            roles: Roles a los que aplica

        Returns:
            RowLevelSecurityPolicy: La política creada
        """
        return RowLevelSecurityPolicy.objects.create(
            table_name=table_name,
            policy_name=policy_name,
            policy_type=RowLevelSecurityPolicy.PolicyTypes.SELECT,
            using_expression=using_expression,
            roles=roles or [],
        )

    @staticmethod
    def create_insert_update_policy(
        table_name: str,
        policy_name: str,
        using_expression: str,
        with_check_expression: str,
        roles: List[str] = None,
    ) -> RowLevelSecurityPolicy:
        """
        Crea una política RLS para INSERT/UPDATE.

        Args:
            table_name: Nombre de la tabla
            policy_name: Nombre de la política
            using_expression: Expresión SQL para USING clause
            with_check_expression: Expresión SQL para WITH CHECK clause
            roles: Roles a los que aplica

        Returns:
            RowLevelSecurityPolicy: La política creada
        """
        return RowLevelSecurityPolicy.objects.create(
            table_name=table_name,
            policy_name=policy_name,
            policy_type=RowLevelSecurityPolicy.PolicyTypes.ALL,
            using_expression=using_expression,
            with_check_expression=with_check_expression,
            roles=roles or [],
        )

    @staticmethod
    def apply_row_level_security(
        user: User,
        queryset: QuerySet,
        permission_codename: str = None,
    ) -> QuerySet:
        """
        Aplica filtros RLS a un QuerySet basado en permisos del usuario.

        Args:
            user: Usuario
            queryset: QuerySet a filtrar
            permission_codename: Codename del permiso requerido

        Returns:
            QuerySet: QuerySet filtrado
        """
        # Superusers ven todo
        if user.is_superuser:
            return queryset

        # Verificar permisos del usuario
        if permission_codename:
            if not RBACService.check_permission(user, permission_codename):
                return queryset.none()

        # Si no hay permiso específico, aplicar filtro por objeto permitido
        model_class = queryset.model
        content_type = ContentType.objects.get_for_model(model_class)

        permitted_ids = ObjectPermission.objects.filter(
            user=user,
            content_type=content_type,
        ).values_list('object_id', flat=True)

        return queryset.filter(pk__in=permitted_ids)
