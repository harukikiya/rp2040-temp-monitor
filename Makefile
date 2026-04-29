.PHONY: html clean serve sync

sync:
	uv sync

html: synv
	uv run sphinx-build -b html -W docs _build/html

clean:
	rm -rf _build/

serve: html
	@echo "Open: http://localhost:8080"
	@uv run python -m http.server -d _build/html 8080