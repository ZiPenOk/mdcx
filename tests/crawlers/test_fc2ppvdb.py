import pytest

from mdcx.config.enums import FieldRule, Language
from mdcx.config.manager import manager
from mdcx.crawlers.fc2ppvdb import Fc2ppvdbCrawler, cookie_str_to_dict, parse_fc2cmadb_html
from mdcx.models.types import CrawlerInput

FC2CMADB_LEGACY_HTML = """
<!DOCTYPE html>
<html>
  <head><title>4930958 作品 - FC2CMADB</title></head>
  <body>
    <h1>
      【ＳＳ超絶美女の美裸体。】超有名タレントファッションモデル。圧倒的スタイルと洗練されたエロス。彼氏に内緒でオトコを惑わす熱くキツイ膣内に精液をぶちまける。
      <a>コメント (4)</a>
    </h1>
    <img src="https://contents-thumbnail2.fc2.com/w276/storage201000.contents.fc2.com/file/286/28519270/1782884209.09.jpg">
    <table>
      <tr><th>ID：</th><td>4930958 复制番号</td></tr>
      <tr><th>販売者：</th><td>KING POWER D</td></tr>
      <tr><th>女優：</th><td>高瀬佳澄</td></tr>
      <tr><th>モザイク：</th><td>無</td></tr>
      <tr><th>販売日：</th><td>2026-07-01</td></tr>
      <tr><th>収録時間：</th><td>01:30:49</td></tr>
      <tr><th>タグ：</th><td>ハメ撮り 美乳 中出し オリジナル 美脚 スレンダー 口内発射 美尻</td></tr>
    </table>
  </body>
</html>
"""


class FakeFc2ppvdbClient:
    def __init__(self):
        self.article_requested = False

    async def request(self, method, url, **kwargs):
        assert method == "GET"
        if url == "https://fc2ppvdb.com/articles/3259498":
            self.article_requested = True

            class ArticleResponse:
                status_code = 200

            return ArticleResponse(), ""

        assert self.article_requested is True
        assert url == "https://fc2ppvdb.com/articles/article-info?videoid=3259498"

        class XhrResponse:
            status_code = 200
            headers = {"content-type": "application/json"}

            def json(self):
                return {
                    "article": {
                        "title": "FC2 Sample",
                        "image_url": "https://example.test/cover.jpg",
                        "release_date": "2026-04-02",
                        "actresses": [{"name": "演员A"}],
                        "tags": [{"name": "無修正"}, {"name": "素人"}],
                        "writer": {"name": "卖家"},
                        "censored": "無",
                        "duration": "01:05:30",
                    }
                }

        return XhrResponse(), ""


class FakeFc2ppvdbHtmlClient:
    async def request(self, method, url, **kwargs):
        assert method == "GET"

        if url == "https://fc2ppvdb.com/articles/3259498":

            class ArticleResponse:
                status_code = 200

            return ArticleResponse(), ""

        class XhrResponse:
            status_code = 200
            headers = {"content-type": "text/html; charset=UTF-8"}
            text = "<!DOCTYPE html><html><title>FC2PPVDB</title><body>ログイン</body></html>"

            def json(self):
                raise ValueError("Expecting value: line 1 column 1 (char 0)")

        return XhrResponse(), ""


class FakeFc2cmadbClient:
    def __init__(self, html_text: str):
        self.html_text = html_text

    async def request(self, method, url, **kwargs):
        assert method == "GET"
        assert url == "https://fc2cmadb.com/articles/4930958"

        class ArticleResponse:
            status_code = 200
            headers = {"content-type": "text/html; charset=UTF-8"}

            def __init__(self, text: str):
                self.text = text

        return ArticleResponse(self.html_text), ""


@pytest.mark.asyncio
async def test_fc2ppvdb_crawler_uses_article_then_xhr(monkeypatch):
    monkeypatch.setattr(manager.config, "fields_rule", "")
    client = FakeFc2ppvdbClient()
    crawler = Fc2ppvdbCrawler(client=client, base_url="https://fc2ppvdb.com")
    res = await crawler.run(
        CrawlerInput(
            appoint_number="",
            appoint_url="",
            file_path=None,
            mosaic="",
            number="FC2-PPV-3259498",
            short_number="FC2-PPV-3259498",
            language=Language.UNDEFINED,
            org_language=Language.UNDEFINED,
        )
    )

    assert res.debug_info.error is None
    assert res.data is not None
    assert res.data.number == "FC2-3259498"
    assert res.data.title == "FC2 Sample"
    assert res.data.actors == ["演员A"]
    assert res.data.tags == ["素人"]
    assert res.data.runtime == "65"
    assert res.data.mosaic == "无码"
    assert res.data.external_id == "https://fc2ppvdb.com/articles/3259498"


@pytest.mark.asyncio
async def test_fc2ppvdb_crawler_parses_fc2cmadb_article_html(monkeypatch):
    monkeypatch.setattr(manager.config, "fields_rule", "")
    crawler = Fc2ppvdbCrawler(client=FakeFc2cmadbClient(FC2CMADB_LEGACY_HTML))
    res = await crawler.run(
        CrawlerInput(
            appoint_number="",
            appoint_url="",
            file_path=None,
            mosaic="",
            number="FC2-4930958",
            short_number="FC2-4930958",
            language=Language.UNDEFINED,
            org_language=Language.UNDEFINED,
        )
    )

    assert res.debug_info.error is None
    assert res.data is not None
    assert res.data.number == "FC2-4930958"
    assert res.data.title == (
        "【ＳＳ超絶美女の美裸体。】超有名タレントファッションモデル。"
        "圧倒的スタイルと洗練されたエロス。彼氏に内緒でオトコを惑わす"
        "熱くキツイ膣内に精液をぶちまける。"
    )
    assert res.data.actors == ["高瀬佳澄"]
    assert res.data.tags == ["ハメ撮り", "美乳", "中出し", "オリジナル", "美脚", "スレンダー", "口内発射", "美尻"]
    assert res.data.studio == "KING POWER D"
    assert res.data.publisher == "KING POWER D"
    assert res.data.release == "2026-07-01"
    assert res.data.year == "2026"
    assert res.data.runtime == "90"
    assert res.data.mosaic == "无码"
    assert (
        res.data.thumb
        == "https://contents-thumbnail2.fc2.com/w276/storage201000.contents.fc2.com/file/286/28519270/1782884209.09.jpg"
    )
    assert res.data.poster == res.data.thumb
    assert res.data.external_id == "https://fc2cmadb.com/articles/4930958"


@pytest.mark.asyncio
async def test_fc2ppvdb_crawler_can_use_fc2cmadb_seller_as_actor(monkeypatch):
    monkeypatch.setattr(manager.config, "fields_rule", [FieldRule.FC2_SELLER])
    crawler = Fc2ppvdbCrawler(client=FakeFc2cmadbClient(FC2CMADB_LEGACY_HTML))
    res = await crawler.run(
        CrawlerInput(
            appoint_number="",
            appoint_url="",
            file_path=None,
            mosaic="",
            number="FC2-4930958",
            short_number="FC2-4930958",
            language=Language.UNDEFINED,
            org_language=Language.UNDEFINED,
        )
    )

    assert res.debug_info.error is None
    assert res.data is not None
    assert res.data.actors == ["KING POWER D"]


def test_fc2ppvdb_cookie_parser_accepts_cookie_without_spaces():
    assert cookie_str_to_dict("foo=bar;fc2ppvdb_session=abc; theme=dark") == {
        "foo": "bar",
        "fc2ppvdb_session": "abc",
        "theme": "dark",
    }


def test_fc2cmadb_parser_reads_inertia_article_json():
    html_text = """
    <!DOCTYPE html>
    <html>
      <head><title inertia>FC2CMADB</title></head>
      <body>
        <script data-page="app" type="application/json">
          {
            "component": "Articles/Show",
            "props": {
              "article": {
                "title": "FC2CMADB Inertia Sample",
                "video_id": 4930958,
                "censored": "無",
                "release_date": "2026-07-01",
                "duration": "01:30:49",
                "image_url": "https://contents-thumbnail2.fc2.com/sample.jpg",
                "writer": {"name": "KING POWER D"},
                "tags": [{"name": "ハメ撮り"}, {"name": "美乳"}]
              }
            }
          }
        </script>
      </body>
    </html>
    """

    data = parse_fc2cmadb_html(html_text, base_url="https://fc2cmadb.com", number="4930958")

    assert data is not None
    assert data["article"]["title"] == "FC2CMADB Inertia Sample"
    assert data["article"]["video_id"] == "4930958"
    assert data["article"]["image_url"] == "https://contents-thumbnail2.fc2.com/sample.jpg"
    assert data["article"]["writer"] == {"name": "KING POWER D"}
    assert data["article"]["tags"] == [{"name": "ハメ撮り"}, {"name": "美乳"}]


def test_fc2cmadb_parser_rejects_inertia_shell_without_article_data():
    html_text = """
    <!DOCTYPE html>
    <html>
      <head><title inertia>FC2CMADB</title></head>
      <body>
        <script data-page="app" type="application/json">
          {"component": "Articles/Show", "props": {"appName": "FC2CMADB"}}
        </script>
      </body>
    </html>
    """

    assert parse_fc2cmadb_html(html_text, base_url="https://fc2cmadb.com", number="4930958") is None


@pytest.mark.asyncio
async def test_fc2ppvdb_crawler_reports_login_page_xhr(monkeypatch):
    monkeypatch.setattr(manager.config, "fields_rule", "")
    crawler = Fc2ppvdbCrawler(client=FakeFc2ppvdbHtmlClient(), base_url="https://fc2ppvdb.com")
    res = await crawler.run(
        CrawlerInput(
            appoint_number="",
            appoint_url="",
            file_path=None,
            mosaic="",
            number="FC2-3259498",
            short_number="FC2-3259498",
            language=Language.UNDEFINED,
            org_language=Language.UNDEFINED,
        )
    )

    assert res.data is None
    assert res.debug_info.error is not None
    assert "fc2ppvdb Cookie 可能无效或已过期" in str(res.debug_info.error)
