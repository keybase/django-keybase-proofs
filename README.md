# django-keybase-proofs

[![PyPI version](https://badge.fury.io/py/keybase-proofs.svg?maxAge=2592000)](https://badge.fury.io/py/keybase-proofs)
[![PyPI](https://img.shields.io/pypi/pyversions/keybase-proofs.svg)](https://pypi.python.org/pypi/keybase-proofs)
[![Travis CI](https://travis-ci.org/keybase/django-keybase-proofs.svg?branch=master)](https://travis-ci.org/keybase/django-keybase-proofs)

`keybase-proofs` is a Django application and reference implementation for
integrating Keybase proofs into a web app.. If you are looking to integrate
Keybase proofs into your application and you use Django, you can use this as a
drop-in library. Otherwise, you can [run the server
locally](##exploring-the-example-service) or checkout the code to see how to
build your own integration. You can read the [full integration
documentation](https://keybase.io/docs/proof_service) for all of the required
steps to integrate with Keybase.

The library supports Django 1.11 to Django 2.1 across Python versions 2.7 to
3.7. If you would like to see a feature or find a bug, please let us know by
opening an [issue](https://github.com/keybase/keybase-proofs/issues) or [pull
request](https://github.com/keybase/keybase-proofs/pulls).

## Integrate with an existing django application

To install:

```
pip install keybase-proofs
```

Add `keybase_proofs` to settings.py's `INSTALLED_APPS`:

```python
INSTALLED_APPS = (
    # ...other installed applications...
    'keybase_proofs',
)
```

Add `url(r'^keybase_proofs/', include('keybase_proofs.urls')),` to your main
`urls.py`

You can copy the example templates in `keybase_proofs/templates/` to customize
and style as necessary. Checkout the [remaining
steps](https://keybase.io/docs/proof_service#4-steps-to-rollout) to integrate
and submit your configuration to Keybase.

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
