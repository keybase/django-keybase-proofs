# django-keybase-proofs

[![PyPI version](https://badge.fury.io/py/django-keybase-proofs.svg?maxAge=2592000)](https://badge.fury.io/py/django-keybase-proofs)
[![PyPI](https://img.shields.io/pypi/pyversions/django-keybase-proofs.svg)](https://pypi.python.org/pypi/django-keybase-proofs)
[![Travis CI](https://travis-ci.org/keybase/django-keybase-proofs.svg?branch=master)](https://travis-ci.org/keybase/django-keybase-proofs)
[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)

`django-keybase-proofs` is a Django application and reference implementation
for integrating Keybase proofs into a web app. If you are looking to integrate
Keybase proofs into your application and you use Django, you can use this as a
drop-in library. Otherwise, you can [run the server
locally](##exploring-the-example-service) or checkout the code to see how to
build your own integration. You can read the [full integration
documentation](https://keybase.io/docs/proof_integration_guide) for all of the
required steps to integrate with Keybase.

The library supports Django 1.11 to Django 2.2 across Python versions 2.7 to
3.7. If you would like to see a feature or find a bug, please let us know by
opening an [issue](https://github.com/keybase/keybase-proofs/issues) or [pull
request](https://github.com/keybase/keybase-proofs/pulls).

## Integrate with an existing django application

To install:

```
pip install django-keybase-proofs
```

Add `keybase_proofs` to settings.py's `INSTALLED_APPS` and set the
`KEYBASE_PROOFS_DOMAIN` settings:

```python
INSTALLED_APPS = (
    # ...other installed applications...
    'keybase_proofs',
)
# Must match the `domain` set in the config.
KEYBASE_PROOFS_DOMAIN = <your-domain.com>
```

Add `url(r'^keybase_proofs/', include('keybase_proofs.urls')),` to your main
`urls.py`

You can copy the example templates in `keybase_proofs/templates/` to customize
and style as necessary. Checkout the [remaining
steps](https://keybase.io/docs/proof_integration_guide#4-steps-to-rollout) to
integrate and submit your configuration to Keybase.

NOTE: In the integration guide [periodic
checking](https://keybase.io/docs/proof_integration_guide#3-linking-user-profiles)
of the proof's liveness is discussed. This library does not implement the this
behavior since there is not an generic way to express this for Django
applications. We provide a library function
(`keybase_proofs.views.verify_proof`) to implement this functionality if
desired. The job scheduling/retry behavior is left up to the implementation.


## Exploring the example service

If you are building a Keybase proof integration but don't use Django, you can
still use this package as an reference implementation. Using the instructions
below you can run the server locally to see expected behavior/responses you
should implement.

First install the required python packages with:

```
# install basic python requirements, a virtualenv is recommended.
make installdeps
# Run the example `test_app` server
make run
```

When running the test server you can play around with posting proofs/reading
the API. The test server does not have any authentication mechanism. Any
username you submit on the login form will be authenticated and can post a
proof.


## Example config

Here is an example configuration if you were to use this library. You should
check out [the
documentation](https://keybase.io/docs/proof_integration_guide#1-config) for
the complete description of what's going on here.

```json
{
  "version": 1,
  "domain": "<your-domain.com>",
  "display_name": "Django Keybase Proofs",
  "username": {
    "re": "^[a-zA-Z0-9_]{2,20}$",
    "min": 2,
    "max": 20
  },
  "brand_color": "#000100",
  "logo": null,
  "description": "Next gen social network using big data & AI in the cloud 🤖☁️.",
  "prefill_url": "https://<your-domain.com>/keybase-proofs/new-proof?kb_username=%{kb_username}&username=%{username}&sig_hash=%{sig_hash}&kb_ua=%{kb_ua}",
  "profile_url": "https://<your-domain.com>/keybase-proofs/profile/%{username}",
  "check_url": "https://<your-domain.com>/keybase-proofs/api/%{username}",
  "check_path": ["keybase_sigs"],
  "contact": ["admin@<your-domain.com>", "joshblum@keybase"]
}
```

## Verifying the integration

While integrating you can use the [verification
script](https://keybase.io/docs/proof_integration_guide/verification_script) to
help manually verify the correctness your integration.

## Development tips

You can run tests by running:
```
    make test
```

To release to pypi:
```
TAG_NAME="XXX"
make release TAG_NAME=$TAG_NAME
```
