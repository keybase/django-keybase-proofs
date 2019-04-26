from copy import copy
from operator import itemgetter

from django.conf import settings
from django.test import TestCase
from django.urls import reverse

from keybase_proofs.users import UserModel
from keybase_proofs.views import is_proof_live

try:
    from unittest.mock import MagicMock
    from unittest.mock import patch
    from urllib.parse import quote_plus
except ImportError:
    from mock import MagicMock
    from mock import patch
    from urllib import quote_plus


class TestViews(TestCase):

    @patch('requests.get')
    def test_is_proof_live(self, mock_requests):
        mock_requests.return_value = MagicMock(status_code=200,
                                               json=lambda: {'proof_valid': True, 'proof_live': True})
        username = 'bob'
        password = 'bobo'
        user = UserModel().objects.create_user(username, 'bob@bob.com', password)

        proof_valid, proof_live = is_proof_live(user, 'sig_hash', 'kb_username')
        self.assertEqual(proof_valid, True)
        self.assertEqual(proof_live, True)

        mock_requests.return_value = MagicMock(status_code=200,
                                               json=lambda: 'invalid')
        proof_valid, proof_live = is_proof_live(user, 'sig_hash', 'kb_username')
        self.assertEqual(proof_valid, False)
        self.assertEqual(proof_live, False)

        mock_requests.return_value = MagicMock(status_code=400,
                                               json=lambda: {'proof_valid': False, 'proof_live': False})
        proof_valid, proof_live = is_proof_live(user, 'sig_hash', 'kb_username')
        self.assertEqual(proof_valid, False)
        self.assertEqual(proof_live, False)

    @patch('requests.get')
    def test_views(self, mock_requests):
        mock_requests.return_value = MagicMock(status_code=200,
                                               json=lambda: {'proof_valid': True})

        # non-existent user gives a 404
        username = 'bob'
        password = 'bobo'
        list_proofs_url = reverse('keybase_proofs:list-proofs-api', kwargs={'username': username})
        resp = self.client.get(list_proofs_url)
        self.assertEqual(resp.status_code, 404)

        # valid user with no proofs gives an empty response
        UserModel().objects.create_user(username, 'bob@bob.com', password)
        resp = self.client.get(list_proofs_url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {'keybase_sigs': []})

        self.client.login(username=username, password=password)

        # username, kb_username, and sig_hash are all required.
        resp = self.client.post(reverse('keybase_proofs:new-proof'))
        self.assertEqual(resp.status_code, 400)
        mock_requests.assert_not_called()

        kb_ua = quote_plus('darwin:Keybase CLI (go1.10.3):2.11.0')
        domain = quote_plus(settings.KEYBASE_PROOFS_DOMAIN)
        resp = self.client.post(reverse('keybase_proofs:new-proof'), data={
            'kb_username': 'kb_{}'.format(username),
        })
        self.assertEqual(resp.status_code, 400)
        mock_requests.assert_not_called()

        resp = self.client.post(reverse('keybase_proofs:new-proof'), data={
            'sig_hash': 'abc123',
        })
        self.assertEqual(resp.status_code, 400)
        mock_requests.assert_not_called()

        # sig_hash must be a hex string
        resp = self.client.post(reverse('keybase_proofs:new-proof'), data={
            'username': username,
            'kb_username': 'kb_{}'.format(username),
            'sig_hash': 'NOT_HEX',
        })
        self.assertEqual(resp.status_code, 400)
        mock_requests.assert_not_called()

        # username must match logged in user
        resp = self.client.post(reverse('keybase_proofs:new-proof'), data={
            'username': 'fake_{}'.format(username),
            'kb_username': 'kb_{}'.format(username),
            'sig_hash': 'abc123',
        })
        self.assertEqual(resp.status_code, 400)
        mock_requests.assert_not_called()

        # post a valid proof
        valid_data = {
            'username': username,
            'kb_username': 'kb_{}'.format(username),
            'sig_hash': 'abc123',
            'kb_ua': kb_ua,
        }
        resp = self.client.post(reverse('keybase_proofs:new-proof'), data=valid_data)
        self.assertEqual(resp.status_code, 301)
        kb_redirect_endpoint_tpl = "https://keybase.io/_/proof_creation_success?kb_ua={kb_ua}&kb_username={kb_username}&sig_hash={sig_hash}&username={username}&domain={domain}"
        self.assertEqual(resp.url, kb_redirect_endpoint_tpl.format(
            domain=domain, **valid_data))

        kb_endpoint = "https://keybase.io/_/api/1.0/sig/proof_valid.json"
        mock_requests.assert_called_once_with(kb_endpoint, params={
            'domain': settings.KEYBASE_PROOFS_DOMAIN,
            'kb_username': valid_data['kb_username'],
            'username': username,
            'sig_hash': valid_data['sig_hash']
        })
        mock_requests.reset_mock()

        resp = self.client.get(list_proofs_url)
        self.assertEqual(resp.status_code, 200)
        expected_response = copy(valid_data)
        del expected_response['kb_ua']
        del expected_response['username']
        self.assertEqual(resp.json(), {'keybase_sigs': [expected_response]})

        # update sig_hash
        valid_data['sig_hash'] = valid_data['sig_hash'] + '123'
        resp = self.client.post(reverse('keybase_proofs:new-proof'), data=valid_data)
        self.assertEqual(resp.status_code, 301)
        self.assertEqual(resp.url, kb_redirect_endpoint_tpl.format(
            domain=domain, **valid_data))

        mock_requests.assert_called_once_with(kb_endpoint, params={
            'domain': settings.KEYBASE_PROOFS_DOMAIN,
            'kb_username': valid_data['kb_username'],
            'username': username,
            'sig_hash': valid_data['sig_hash']
        })
        mock_requests.reset_mock()

        resp = self.client.get(list_proofs_url)
        self.assertEqual(resp.status_code, 200)
        expected_response = copy(valid_data)
        del expected_response['kb_ua']
        del expected_response['username']
        self.assertEqual(resp.json(), {'keybase_sigs': [expected_response]})

        # add second proof
        valid_data2 = {
            'username': username,
            'kb_username': 'kb2_{}'.format(username),
            'sig_hash': 'abc123',
            'kb_ua': kb_ua,
        }
        resp = self.client.post(reverse('keybase_proofs:new-proof'), data=valid_data2)
        self.assertEqual(resp.status_code, 301)
        self.assertEqual(resp.url, kb_redirect_endpoint_tpl.format(
            domain=domain, **valid_data2))

        mock_requests.assert_called_once_with(kb_endpoint, params={
            'domain': settings.KEYBASE_PROOFS_DOMAIN,
            'username': username,
            'kb_username': valid_data2['kb_username'],
            'sig_hash': valid_data2['sig_hash']
        })
        mock_requests.reset_mock()

        resp = self.client.get(list_proofs_url)
        self.assertEqual(resp.status_code, 200)
        resp_proofs = resp.json().get('keybase_sigs', [])
        expected_response2 = copy(valid_data2)
        del expected_response2['kb_ua']
        del expected_response2['username']
        self.assertEqual(sorted(resp_proofs, key=itemgetter('kb_username')),
                         sorted([expected_response, expected_response2], key=itemgetter('kb_username')))

        # simple get on profile page
        resp = self.client.get(reverse('keybase_proofs:profile', kwargs={'username': username}))
        self.assertEqual(resp.status_code, 200)

        resp = self.client.get(reverse('keybase_proofs:new-proof'))
        self.assertEqual(resp.status_code, 200)
