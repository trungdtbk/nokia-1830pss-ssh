test:
	python -m pytest --cov=pss1830ssh --cov-report term-missing --pylint --pylint-error-types=EF

lint:
	pylint pssexec/ tests/

checklist: lint test

.PHONY: test lint checklist