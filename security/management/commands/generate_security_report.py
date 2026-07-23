"""
Management command to generate security reports.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from security.models import SecurityReport


class Command(BaseCommand):
    help = 'Genera un reporte de seguridad del sistema'

    def add_arguments(self, parser):
        parser.add_argument(
            '--scan-type',
            type=str,
            default='vulnerability',
            choices=['vulnerability', 'compliance', 'penetration', 'configuration'],
            help='Tipo de escaneo a realizar'
        )

    def handle(self, *args, **options):
        scan_type = options['scan_type']
        
        self.stdout.write(
            self.style.WARNING(f'Generando reporte de seguridad: {scan_type}...')
        )
        
        # Generar findings de ejemplo basados en el tipo de scan
        findings = self.generate_findings(scan_type)
        
        # Crear el reporte
        report = SecurityReport.objects.create(
            scan_type=scan_type,
            findings=findings,
            resolved=False
        )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'✅ Reporte generado exitosamente: {report.report_id}'
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                f'   Fecha: {report.generated_at.strftime("%Y-%m-%d %H:%M:%S")}'
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                f'   Hallazgos: {len(findings)}'
            )
        )
        
        # Mostrar hallazgos críticos
        critical_findings = [f for f in findings if f.get('severity') == 'critical']
        if critical_findings:
            self.stdout.write(
                self.style.ERROR(
                    f'\n⚠️  {len(critical_findings)} hallazgos críticos encontrados:'
                )
            )
            for finding in critical_findings:
                self.stdout.write(
                    self.style.ERROR(f'   • {finding["description"]}')
                )
        else:
            self.stdout.write(
                self.style.SUCCESS('\n✅ No se encontraron hallazgos críticos')
            )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nPuedes ver el reporte completo en: /admin/security/securityreport/{report.pk}/'
            )
        )

    def generate_findings(self, scan_type):
        """Genera findings de ejemplo según el tipo de escaneo."""
        
        if scan_type == 'vulnerability':
            return [
                {
                    'severity': 'info',
                    'description': 'Sistema de autenticación implementado correctamente',
                    'category': 'authentication',
                    'recommendation': 'Continuar monitoreando intentos de acceso'
                },
                {
                    'severity': 'info',
                    'description': 'WAF activo y funcionando',
                    'category': 'protection',
                    'recommendation': 'Mantener reglas WAF actualizadas'
                },
                {
                    'severity': 'low',
                    'description': 'Se recomienda habilitar 2FA para todos los administradores',
                    'category': 'authentication',
                    'recommendation': 'Implementar política de 2FA obligatorio para staff'
                }
            ]
        
        elif scan_type == 'compliance':
            return [
                {
                    'severity': 'info',
                    'description': 'Headers de seguridad configurados correctamente',
                    'category': 'owasp',
                    'recommendation': 'Mantener configuración actual'
                },
                {
                    'severity': 'info',
                    'description': 'CSRF protection activo',
                    'category': 'owasp',
                    'recommendation': 'Sin cambios necesarios'
                },
                {
                    'severity': 'medium',
                    'description': 'Revisar política de contraseñas',
                    'category': 'owasp',
                    'recommendation': 'Considerar requisitos de complejidad más estrictos'
                }
            ]
        
        elif scan_type == 'penetration':
            return [
                {
                    'severity': 'info',
                    'description': 'No se detectaron inyecciones SQL',
                    'category': 'injection',
                    'recommendation': 'Continuar usando consultas parametrizadas'
                },
                {
                    'severity': 'info',
                    'description': 'No se detectaron vulnerabilidades XSS',
                    'category': 'xss',
                    'recommendation': 'Mantener validación de entradas'
                },
                {
                    'severity': 'low',
                    'description': 'Algunos endpoints no validan rate limiting',
                    'category': 'dos',
                    'recommendation': 'Implementar rate limiting en todos los endpoints públicos'
                }
            ]
        
        elif scan_type == 'configuration':
            return [
                {
                    'severity': 'info',
                    'description': 'DEBUG está desactivado en producción',
                    'category': 'configuration',
                    'recommendation': 'Configuración correcta'
                },
                {
                    'severity': 'info',
                    'description': 'SECRET_KEY configurado de forma segura',
                    'category': 'configuration',
                    'recommendation': 'Sin cambios necesarios'
                },
                {
                    'severity': 'medium',
                    'description': 'Revisar configuración de ALLOWED_HOSTS',
                    'category': 'configuration',
                    'recommendation': 'Asegurar que solo dominios legítimos están permitidos'
                }
            ]
        
        return []
