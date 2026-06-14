from django.contrib.auth.models import Group


def group_name(request):
    """
    Context processor para agregar el nombre del grupo del usuario a todas las plantillas.
    """
    context = {'group_name': None, 'is_editor': False}
    
    if request.user.is_authenticated:
        groups = list(request.user.groups.values_list('name', flat=True))
        group = Group.objects.filter(user=request.user).first()
        if group:
            context['group_name'] = group.name
        context['is_editor'] = 'Editor' in groups
    
    return context
