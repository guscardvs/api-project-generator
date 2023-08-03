.PHONY: format run-dev test lint

RUN := poetry run

format:
	@echo "Running black"
	@${RUN} black api_project_generator tests

	@echo "Running isort"
	@${RUN} isort api_project_generator tests

	@echo "Running autoflake"
	@${RUN} autoflake --remove-all-unused-imports --remove-unused-variables --remove-duplicate-keys --expand-star-imports -ir api_project_generator tests

