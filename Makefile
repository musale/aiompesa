lint:
	@pipenv run black --line-length=79 --target-version py36 . && flake8 .

upload:
	@rm -rf build
	@rm -rf dist
	@sudo rm -rf aiompesa.egg-info
	@python setup.py sdist
	@python setup.py bdist_wheel
	@pipenv run twine upload -u ${TWINE_USERNAME} -p ${TWINE_PASSWORD} dist/*

.PHONY: tests
tests:
	@pipenv run pytest --verbose

.PHONY: build
build:
	@pipenv run sphinx-build -a -E docs/source docs/build
