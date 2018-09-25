from django.contrib.auth import get_user_model
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.views import LoginView as AuthLoginView
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView


@method_decorator(csrf_exempt, name='dispatch')
class LoginView(TemplateView):
    """
    In this *example* server, visiting login with a given username will
    authenticate you as that user to allow freedom of testing. If the user does
    not exist, it is created.
    """
    template_name = 'login.html'

    def get_success_url(self, username):
        return reverse('keybase_proofs:profile', kwargs={
            'username': username
        })

    def post(self, request, *args, **kwargs):
        UserModel = get_user_model()
        username = request.POST.get('username', self.kwargs.get('username', ''))
        if not username:
            return redirect(reverse('auth_login'))

        user, _ = UserModel.objects.get_or_create(username=username)
        auth_login(self.request, user)
        redirect_to = self.request.POST.get('next')
        if not redirect_to:
            redirect_to = self.request.GET.get('next', self.get_success_url(username))
        return redirect(redirect_to)

class LogoutView(View):

    def dispatch(self, request, *args, **kwargs):
        auth_logout(request)
        return redirect(reverse('index'))
