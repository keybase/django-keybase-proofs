import re

import requests
from jsonview.views import JsonView
from py2casefold import casefold

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ImproperlyConfigured
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
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


def is_proof_valid(username, sig_hash, kb_username):
    """
    Check the proof validity in Keybase via the `sig/proof_valid` endpoint.
    Returns a boolean `proof_valid` indicating if the signature is valid for
    the given domain/kb_username/username/sig_hash combination.

    Before storing a signature `proof_valid=True` must hold.
    """

    domain = get_domain()
    endpoint = "https://keybase.io/_/api/1.0/sig/proof_valid.json"
    try:
        r = requests.get(endpoint, params={
            'domain': domain,
            'username': username,
            'kb_username': kb_username,
            'sig_hash': sig_hash,
        })
        if r.status_code != 200:
            print("Invalid response:", r)
            return False
        r_json = r.json()
        return r_json.get('proof_valid', False)
    except Exception:
        return False


def is_proof_live(user, sig_hash, kb_username):
    """
    Checks the proof status in Keybase via the `sig/proof_live` endpoint.
    Returns a tuple (`proof_valid`, `proof_live`) indicating if the signature
    is live and if the proof is publicly verifiable to the Keybase
    client/server, respectively.

    Keybase suggests an asynchronous task that calls this endpoint during the
    proof creation flow. It will return (proof_valid=True, proof_live=False)
    until Keybase has seen it being served from this service's API, at which
    point it will update to (proof_valid=True, proof_live=True). This is the
    happy path.  It may also make sense to call this endpoint periodically or
    whenever a user inspects their own proof/profile/settings to update local
    records.  If a user revokes their proof from Keybase, this will return
    (profo_valid=False, proof_live=False).
    """
    domain = get_domain()
    endpoint = "https://keybase.io/_/api/1.0/sig/proof_live.json"
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
        return r_json.get('proof_valid', False), r_json.get('proof_live', False)
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

    def get_redirect_url(self, **kwargs):
        return "https://keybase.io/_/proof_creation_success?kb_ua={kb_ua}&kb_username={kb_username}&sig_hash={sig_hash}&username={username}&domain={domain}".format(**kwargs)

    def username_eq(self, u1, u2):
        """
        Force each username to lowercase and compare them. Can be overridden if
        the service has case sensitive usernames.
        """
        return casefold(u1) == casefold(u2)

    def _validate(self, user, username, sig_hash, kb_username):
        error = None
        if not all([username, sig_hash, kb_username]):
            error = 'username, sig_hash, and kb_username query parameters are required'
        elif not self.username_eq(user.username, username):
            error = 'please logout from {} and login as {}'.format(user.username, username)
        elif not self._is_hex(sig_hash):
            error = 'sig_hash must be a hex string'
        return error

    def get(self, request, *args, **kwargs):
        sig_hash = request.GET.get('sig_hash')
        kb_username = request.GET.get('kb_username')
        kb_ua = request.GET.get('kb_ua')
        username = request.GET.get('username')
        error = self._validate(request.user, username, sig_hash, kb_username)
        return render(request, self.template_name, {
            'sig_hash': sig_hash,
            'kb_username': kb_username,
            'kb_ua': kb_ua,
            'error': error
        })

    def post(self, request, *args, **kwargs):
        sig_hash = request.POST.get('sig_hash')
        kb_username = request.POST.get('kb_username')
        username = request.POST.get('username')
        kb_ua = request.POST.get('kb_ua')
        error = self._validate(request.user, username, sig_hash, kb_username)
        if error is None:
            proof_valid = is_proof_valid(username, sig_hash, kb_username)
            if not proof_valid:
                error = "Invalid signature, please retry"
            else:
                kb_proof, created = KeybaseProof.objects.get_or_create(
                    user=request.user, kb_username=kb_username)
                kb_proof.is_verified = proof_valid
                kb_proof.sig_hash = sig_hash
                kb_proof.save()
                return redirect(self.get_redirect_url(**{
                    'kb_ua': kb_ua,
                    'kb_username': kb_username,
                    'sig_hash': sig_hash,
                    'username': request.user.username,
                    'domain': get_domain(),
                }), permanent=True)

        return render(request, self.template_name, {'error': error}, status=400)
