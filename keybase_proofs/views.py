import re

import requests
from jsonview.views import JsonView

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ImproperlyConfigured
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import ListView

from keybase_proofs.models import KeybaseProof


def fullmatch(regex, string, flags=0):
    """Emulate python-3.4 re.fullmatch()."""
    return re.match("(?:" + regex + r")\Z", string, flags=flags)


def get_domain():
    domain = getattr(settings, 'KEYBASE_PROOFS_DOMAIN')
    if not domain:
        raise ImproperlyConfigured('KEYBASE_PROOFS_DOMAIN must be set when using.')
    return domain


def verify_proof(user, sig_hash, kb_username):
    """
    Check the proof status in Keybase via the `sig/check_proof` endpoint.
    Returns a tuple (valid_proof, proof_live) indicating if the signature is
    valid for the given domain/kb_username/username combination and if the
    proof is publicly verifiable to the Keybase client/server respectively.

    Before storing a signature `valid_proof=True` must hold. Services can
    optionally check the status of signatures periodically and verify
    `proof_live=True` as well.
    """

    domain = get_domain()
    endpoint = "https://keybase.io/_/api/1.0/sig/check_proof.json"
    try:
        r = requests.get(endpoint, params={
            'domain': domain,
            'username': user.username,
            'kb_username': kb_username,
            'sig_hash': sig_hash,
        })
        if r.status_code != 200:
            print("Invalid response:", r)
            return False, False
        r_json = r.json()
        return r_json.get('valid_proof', False), r_json.get('proof_live', False)
    except Exception:
        return False, False


class KeybaseProofProfileView(ListView):
    """
    Example endpoint for showing existing keybase proofs on a user's profile.
    Can be integrated into an existing profile page in production apps.
    """
    model = KeybaseProof
    template_name = 'keybase_proofs/profile.html'

    def get_context_data(self, **kwargs):
        context = super(KeybaseProofProfileView, self).get_context_data(**kwargs)
        context['domain'] = get_domain()
        return context

    def get_queryset(self):
        username = self.kwargs.get('username', '')
        user = get_object_or_404(get_user_model(), username=username)
        queryset = self.model.objects.filter(user=user)
        return queryset


class KeybaseProofListView(JsonView, KeybaseProofProfileView):
    """
    API endpoint that the Keybase servers/clients will use to validate proofs.
    Returns a json list of proofs for the given username. Must be a publicly
    accessible url.
    """

    def get_context_data(self, **kwargs):
        # Will throw a 404 for missing users (from the URL parameter) or return
        # an empty queryset for a valid username.
        queryset = self.get_queryset()
        return {
            'keybase_sigs': [x.to_dict() for x in queryset]
        }


@method_decorator(login_required, name='dispatch')
class KeybaseProofView(View):
    """
    Handles posting a new keybase proof. On GET requests the user can confirm
    the `kb_username` and `sig_hash` posted in the GET parameters from the
    keybase client.  Upon confirmation, the user can POST these to store and
    allow the keybase servers/clients to verify the signature.

    Users can post multiple kb_usernames, and update the sig_hash if they wish
    to repost the proof.

    `sig_hash` must validate as a hex string
    """
    template_name = 'keybase_proofs/profile_confirm.html'

    def _is_hex(self, s):
        return fullmatch(r'^[0-9a-fA-F]+$', s or "") is not None

    def get_success_url(self):
        return reverse('keybase_proofs:profile', kwargs={
            'username': self.request.user.username,
        })

    def _validate(self, sig_hash, kb_username):
        error = None
        if not (sig_hash and kb_username):
            error = 'both sig_hash and kb_username query parameters are required'
        elif not self._is_hex(sig_hash):
            error = 'sig_hash must be a hex string'
        return error

    def get(self, request, *args, **kwargs):
        sig_hash = request.GET.get('sig_hash')
        kb_username = request.GET.get('kb_username')
        error = self._validate(sig_hash, kb_username)
        return render(request, self.template_name, {
            'sig_hash': sig_hash,
            'kb_username': kb_username,
            'error': error
        })

    def post(self, request, *args, **kwargs):
        sig_hash = request.POST.get('sig_hash')
        kb_username = request.POST.get('kb_username')
        error = self._validate(sig_hash, kb_username)
        if error is None:
            valid_proof, _ = verify_proof(request.user, sig_hash, kb_username)
            if not valid_proof:
                error = "Invalid signature, please retry"
            else:
                kb_proof, created = KeybaseProof.objects.get_or_create(
                    user=request.user, kb_username=kb_username)
                kb_proof.is_verified = valid_proof
                kb_proof.sig_hash = sig_hash
                kb_proof.save()
                return redirect(self.get_success_url())

        return render(request, self.template_name, {'error': error}, status=400)
