from operator import itemgetter

from django.conf import settings
from django.test import TestCase
from django.urls import reverse

from keybase_proofs.users import UserModel

try:
    from unittest.mock import MagicMock
    from unittest.mock import patch
except ImportError:
    from mock import MagicMock
    from mock import patch


class TestViews(TestCase):

    @patch('requests.get')
    def test_views(self, mock_requests):
        mock_requests.return_value = MagicMock(status_code=200,
                                               json=lambda: {'valid_proof': True, 'proof_live': False})

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

        # kb_username and sig_hash are both required.
        resp = self.client.post(reverse('keybase_proofs:new-proof'))
        self.assertEqual(resp.status_code, 400)
        mock_requests.assert_not_called()

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
            'kb_username': 'kb_{}'.format(username),
            'sig_hash': 'NOT_HEX',
        })
        self.assertEqual(resp.status_code, 400)
        mock_requests.assert_not_called()

        # post a valid proof
        valid_data = {
            'kb_username': 'kb_{}'.format(username),
            'sig_hash': 'abc123',
        }
        resp = self.client.post(reverse('keybase_proofs:new-proof'), data=valid_data, follow=True)
        self.assertEqual(resp.status_code, 200)
        kb_endpoint = "https://keybase.io/_/api/1.0/sig/check_proof.json"
        mock_requests.assert_called_once_with(kb_endpoint, params={
            'domain': settings.KEYBASE_PROOFS_DOMAIN,
            'kb_username': valid_data['kb_username'],
            'username': username,
            'sig_hash': valid_data['sig_hash']
        })
        mock_requests.reset_mock()

        resp = self.client.get(list_proofs_url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {'keybase_sigs': [valid_data]})

        # update sig_hash
        valid_data['sig_hash'] = valid_data['sig_hash'] + '123'
        resp = self.client.post(reverse('keybase_proofs:new-proof'), data=valid_data, follow=True)
        self.assertEqual(resp.status_code, 200)
        mock_requests.assert_called_once_with(kb_endpoint, params={
            'domain': settings.KEYBASE_PROOFS_DOMAIN,
            'kb_username': valid_data['kb_username'],
            'username': username,
            'sig_hash': valid_data['sig_hash']
        })
        mock_requests.reset_mock()

        resp = self.client.get(list_proofs_url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {'keybase_sigs': [valid_data]})

        # add second proof
        valid_data2 = {
            'kb_username': 'kb2_{}'.format(username),
            'sig_hash': 'abc123',
        }
        resp = self.client.post(reverse('keybase_proofs:new-proof'), data=valid_data2, follow=True)
        self.assertEqual(resp.status_code, 200)
        mock_requests.assert_called_once_with(kb_endpoint, params={
            'domain': settings.KEYBASE_PROOFS_DOMAIN,
            'kb_username': valid_data2['kb_username'],
            'username': username,
            'sig_hash': valid_data2['sig_hash']
        })
        mock_requests.reset_mock()

        resp = self.client.get(list_proofs_url)
        self.assertEqual(resp.status_code, 200)
        resp_proofs = resp.json().get('keybase_sigs', [])
        self.assertEqual(sorted(resp_proofs, key=itemgetter('kb_username')), sorted([valid_data, valid_data2], key=itemgetter('kb_username')))

        # simple get on profile page
        resp = self.client.get(reverse('keybase_proofs:profile', kwargs={'username': username}))
        self.assertEqual(resp.status_code, 200)

        resp = self.client.get(reverse('keybase_proofs:new-proof'))
        self.assertEqual(resp.status_code, 200)
