# -*- coding: utf-8 -*-
"""bug.15 — кеш-политика статики и HTML-страниц.

StaticFiles отдаёт только ETag/Last-Modified, без Cache-Control браузер
складывает JS/CSS в эвристический кеш — после деплоя ученик и тьютор видят
старые student.js/tutor-student.js до жёсткого обновления (Ctrl+Shift+R).
Middleware в webapp/main.py ставит Cache-Control: no-cache, контракт:

  - /static/* → 200 + no-cache (ETag от StaticFiles сохраняется);
  - ревалидация If-None-Match → дешёвый 304, пока файл не менялся;
  - HTML-страницы → no-cache, документ не зависает устаревшим;
  - API/JSON заголовок не получают — вне масштаба бага."""
STATIC_JS = "/static/js/pages/student.js"


class TestCachePolicy:
    def test_static_asset_has_no_cache_header(self, client):
        r = client.get(STATIC_JS)
        assert r.status_code == 200
        assert r.headers["cache-control"] == "no-cache"
        # ETag нужен для ревалидации: без него no-cache превращался бы
        # в полную перезагрузку файла на каждый заход.
        assert r.headers.get("etag")

    def test_static_revalidation_returns_304(self, client):
        etag = client.get(STATIC_JS).headers["etag"]
        r = client.get(STATIC_JS, headers={"if-none-match": etag})
        assert r.status_code == 304
        assert r.headers["cache-control"] == "no-cache"

    def test_html_page_has_no_cache_header(self, client):
        r = client.get("/login")
        assert r.status_code == 200
        assert r.headers["content-type"].startswith("text/html")
        assert r.headers["cache-control"] == "no-cache"

    def test_api_json_has_no_cache_header(self, client, student):
        # 401 без сессии — JSON-ответ без Last-Modified эвристически
        # не кешируется, заголовок ему не положен.
        r = client.get("/api/me")
        assert r.status_code == 401
        assert "cache-control" not in r.headers
