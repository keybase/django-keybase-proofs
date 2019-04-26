.PHONY: installdeps\
		test\
		lint\
		clean \
		release \
		run

installdeps:
	pip install -U -r requirements.txt

test:
	python setup.py test

lint:
	flake8 keybase_proofs
	isort --recursive --check-only keybase_proofs test_app

clean:
	python setup.py clean


release: clean lint test
	ifeq ($(TAG_NAME),)
	$(error Usage: make release TAG_NAME=<tag-name>)
	endif
	# NOTE(joshblum): First you should bump the version in
	# keybase_proofs/__init__.py
	git clean -dxf
	git tag $(TAG_NAME)
	git push --tags
	# To check whether the README formats properly.
	python setup.py check --strict
	# Create the wheels for Python2 and Python3.
	python setup.py sdist bdist_wheel --universal
	# To check whether the README formats properly.
	twine check dist/*
	# Upload to pypi.
	twine upload dist/*

run:
	./manage.py migrate && ./manage.py runserver
