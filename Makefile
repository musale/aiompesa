lint:
	@pipenv run black --line-length=79 --target-version py36 . && flake8 .
