lint:
	@pipenv run black --line-length=79 --target-version py36 . && flake8 .

upload:
	@rm -rf build
	@rm -rf dist
	@sudo rm -rf aiompesa.egg-info
	@python setup.py sdist
	@python setup.py bdist_wheel
	@twine upload dist/*
