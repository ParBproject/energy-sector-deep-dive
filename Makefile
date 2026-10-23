.PHONY: export results test web
results:
	python -m scripts.run_m2 && python -m scripts.run_m3
export:
	python -m src.export.web
test:
	ruff check . && ruff format --check . && pytest -q && cd web && npm test
web: export
	cd web && npm ci && npm run build
