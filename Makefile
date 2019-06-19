lint:
	@pipenv run black --line-length=79 --target-version py36 . && flake8 .

upload:
	@python setup.py sdist bdist_wheel
	@pipenv run twine upload dist/*
