.PHONY: html rebuild clean serve sync

CONF_STAMP := _build/.conf-stamp

sync:
	uv sync

html: sync $(CONF_STAMP)
	uv run sphinx-build -b html -W docs _build/html

# conf.py か ubproject.toml（need の設定）を変更したら _build/ を丸ごと捨てる。
# needs_fields の追加は Sphinx の環境再構築を起こさないため、
# キャッシュが残っているとフィルタが NameError になる。
$(CONF_STAMP): docs/conf.py docs/ubproject.toml
	@echo ">> conf.py または ubproject.toml が更新されたため _build/ を破棄します"
	@rm -rf _build/
	@mkdir -p _build
	@touch $@

rebuild: clean html

clean:
	rm -rf _build/

serve: html
	@echo "Open: http://localhost:8080"
	@uv run python -m http.server -d _build/html 8080