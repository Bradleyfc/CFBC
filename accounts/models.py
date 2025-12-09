from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save

# Create your models here.
# Perfil de registros

class Registro(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='registro', verbose_name='Usuario')
    nacionalidad = models.CharField(max_length=150, null=True, blank = True, verbose_name='Nacionalidad')
    carnet = models.CharField(max_length=11, null=True, blank = True, verbose_name='Carnet')
    foto_carnet = models.ImageField(upload_to='documentos/carnets/', null=True, blank=True, verbose_name='Foto del Carnet')
    SEXO = [
        ('M', 'Masculino'),
        ('F', 'Femenino')
    ]
    sexo = models.CharField(max_length=1, choices=SEXO, default='M', verbose_name='Sexo')

    image = models.ImageField(default='default/plantilla.jpg', upload_to='users/', verbose_name='Imagen de perfil')
    address = models.CharField(max_length=150, null=True, blank = True, verbose_name='Dirección')
    location = models.CharField(max_length=150, null=True, blank = True, verbose_name='Municipio')
    provincia = models.CharField(max_length=150, null=True, blank = True, verbose_name='Provincia')
    telephone = models.CharField(max_length=50, null=True, blank = True, verbose_name='Teléfono')
    movil = models.CharField(max_length=50, null=True, blank = True, verbose_name='Móvil')
    GRADO = [
        ("grado1", "Ninguno"),
        ("grado2", "Noveno Grado"),
        ("grado3", "Bachiller"),
        ("grado4", "Superior"),
    ]
    grado = models.CharField(max_length=50, choices=GRADO, default="grado1")

    OCUPACION =[
        ("ocupacion1", "Desocupado"),
        ("ocupacion2", "Estudiante"),
        ("ocupacion3", "Ama de Casa"),
        ("ocupacion4", "Trabajador Estatal"),
        ("ocupacion5", "Trabajador por Cuenta Propia"),
    ]
    ocupacion = models.CharField(
        max_length=100, choices=OCUPACION, default="ocupacion1", 
    )
    titulo = models.CharField(max_length=150, null=True, blank = True, verbose_name='Título')
    foto_titulo = models.ImageField(upload_to='documentos/titulos/', null=True, blank=True, verbose_name='Foto del Título')
    es_religioso = models.BooleanField(default=False, verbose_name='Es Religioso')
   

    class Meta:
        verbose_name= 'registro'
        verbose_name_plural = 'registros'
        ordering=['-id']

    def __str__(self):
        grupo = self.user.groups.first()
        return f"{self.user.username} - Grupo al que pertenece: {grupo.name if grupo else 'Sin grupo'}"
        


# Las señales se han movido a signals.py para evitar duplicación