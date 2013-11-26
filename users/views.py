from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.forms import EmailField
from django.core.exceptions import ValidationError
from users.models import DareyooUser


@csrf_exempt
def invite_request(request):
    email = request.POST.get('email')
    if request.is_ajax():
        if email and isEmailAddressValid(email):
            if len(DareyooUser.objects.filter(email=email)) > 0:
                return HttpResponse("This email is already registered")
            else:
                u = DareyooUser.objects.create_user(email=request.POST.get('email'))
                u.save()
                return HttpResponse("ok")
        else:
            return HttpResponse("Invalid email")
    else:
        return HttpResponse("Invalid request")

 
def isEmailAddressValid(email):
    try:
        EmailField().clean(email)
        return True
    except ValidationError:
        return False