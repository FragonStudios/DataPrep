.PHONY: test-core test-api test-worker test-ui test-website

test-core:
	python -m pytest packages/core

test-api:
	python -m pytest app/api

test-worker:
	python -m pytest app/worker

test-ui:
	npm --prefix packages/ui test

test-website:
	npm --prefix website test
