lint:
	@pipenv run black --line-length=79 --target-version py36 . && flake8 .

.PHONY: pkg
pkg:
	@rm -rf build
	@rm -rf dist
	@sudo rm -rf aiompesa.egg-info
	@python setup.py sdist
	@python setup.py bdist_wheel

upload:
	@make pkg
	@pipenv run twine upload dist/*

.PHONY: tests
tests:
	@pipenv run pytest --verbose --cov=aiompesa --cov-report html

.PHONY: docs
docs:
	@rm -rf docs/build
	@pipenv run sphinx-build -a -E docs/source docs/build
