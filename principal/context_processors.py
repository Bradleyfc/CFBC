from django.contrib.auth.models import Group


def group_name(request):
    """
    Context processor para agregar el nombre del grupo del usuario a todas las plantillas.
    """
    context = {'group_name': None}
    
    if request.user.is_authenticated:
        group = Group.objects.filter(user=request.user).first()
        if group:
            context['group_name'] = group.name
    
    return context
