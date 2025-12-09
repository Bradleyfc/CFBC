

from django.contrib.auth.models import Group
from django.dispatch import receiver
from django.db.models.signals import post_save
from .models import Registro, User

# aqui se asigna el usurio registrado a un grupo automaticamente
@receiver(post_save, sender=Registro)
def add_user_to_students_group(sender, instance, created, **kwargs):
    if created:
        try:
            students = Group.objects.get(name='Estudiantes')  # nombre del grupo
        except Group.DoesNotExist:
            students = Group.objects.create(name='Estudiantes')
        instance.user.groups.add(students)

#senales para agregar mas campos al modelo de registro de django por defecto
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Registro.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    try:
        if hasattr(instance, 'registro'):
            instance.registro.save()
    except Registro.DoesNotExist:
        # El usuario no tiene registro, no hacer nada
        pass