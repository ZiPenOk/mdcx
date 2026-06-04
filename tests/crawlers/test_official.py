import json

import pytest

from mdcx.config.enums import Language, Website
from mdcx.crawlers.base import get_crawler
from mdcx.crawlers.official import OfficialCrawler
from mdcx.crawlers.official_uncensored import route_uncensored_official
from mdcx.models.types import CrawlerInput


class FakeOfficialClient:
    async def get_text(self, url, **kwargs):
        if url == "https://s1s1s1.com/search/list?keyword=SSIS001":
            return (
                """
                <html><body>
                  <a class="img hover" href="https://s1s1s1.com/works/detail/ssis001">
                    <img data-src="https://example.test/poster.jpg" />
                  </a>
                </body></html>
                """,
                "",
            )
        if url == "https://s1s1s1.com/works/detail/ssis001":
            return _detail_html(), ""
        return None, f"unexpected url: {url}"


class FakeUncensoredOfficialClient:
    def __init__(self):
        self.calls = []

    async def get_text(self, url, **kwargs):
        self.calls.append((url, kwargs))
        if url == "https://www.caribbeancom.com/moviepages/060326-001/index.html":
            return _caribbean_html(), ""
        if url == "https://www.heyzo.com/moviepages/3850/index.html":
            return _heyzo_html(), ""
        if url in _JSON_RESPONSES:
            return json.dumps(_JSON_RESPONSES[url]), ""
        return None, f"unexpected url: {url}"


def _detail_html() -> str:
    return """
    <html>
      <head><meta name="description" content="【公式】Publisher A(Studio A)" /></head>
      <body>
        <h2 class="p-workPage__title">Official Title</h2>
        <a class="c-tag c-main-bg-hover c-main-font c-main-bd" href="/actress/a">Actor A</a>
        <p class="p-workPage__text">Official outline</p>
        <div class="th">収録時間</div><div><div><p>120分</p></div></div>
        <div class="th">シリーズ</div><div><a>Series A</a></div>
        <div class="th">レーベル</div><div><a>Label A</a></div>
        <div class="th">監督</div><div><div><p>Director A</p></div></div>
        <div>発売日</div><div><div><a>2026年04月03日</a></div></div>
        <div>ジャンル</div><div><div><a>Genre A</a><a>Blu-ray（ブルーレイ）</a></div></div>
        <img class="swiper-lazy" data-src="https://example.test/cover.jpg" />
        <img class="swiper-lazy" data-src="https://example.test/extra.jpg" />
        <div class="video"><video src="https://example.test/trailer.mp4"></video></div>
      </body>
    </html>
    """


def _caribbean_html() -> str:
    return """
    <html>
      <body>
        <h1 itemprop="name">Caribbean Title</h1>
        <p itemprop="description">Caribbean outline</p>
        <ul>
          <li class="movie-spec">
            <span class="spec-title">出演</span><span class="spec-content">Actor A, Actor B</span>
          </li>
          <li class="movie-spec">
            <span class="spec-title">配信日</span><span class="spec-content">2026/06/03</span>
          </li>
          <li class="movie-spec">
            <span class="spec-title">再生時間</span><span class="spec-content">01:01:30</span>
          </li>
          <li class="movie-spec">
            <span class="spec-title">タグ</span><span class="spec-content">Tag A, Tag B</span>
          </li>
        </ul>
        <a href="/moviepages/060326-001/images/l/001.jpg">gallery</a>
      </body>
    </html>
    """


def _heyzo_html() -> str:
    return """
    <html>
      <head>
        <script type="application/ld+json">
        {
          "@context": "https://schema.org",
          "@type": "Movie",
          "name": "HEYZO Title",
          "image": "//www.heyzo.com/contents/3000/3850/images/player_thumbnail.jpg",
          "description": "HEYZO outline",
          "actor": {"@type": "Person", "name": "Actor H"},
          "duration": "PT1H1M7S",
          "dateCreated": "2026-05-19T00:00:00+09:00",
          "video": {
            "@type": "VideoObject",
            "contentUrl": "https://sample.heyzo.com/contents/3000/3850/sample.mp4"
          }
        }
        </script>
      </head>
      <body></body>
    </html>
    """


_JSON_RESPONSES = {
    "https://www.1pondo.tv/dyn/phpauto/movie_details/movie_id/053126_001.json": {
        "Title": "1Pondo Title",
        "Actor": "Actor 1",
        "Desc": "1Pondo outline",
        "Duration": 3706,
        "Release": "2026-05-31",
        "Series": "Series 1",
        "UCNAME": "1Pondo",
        "ThumbHigh": "https://www.1pondo.tv/moviepages/053126_001/images/str.jpg",
        "Tag": ["Tag 1", "Tag 2"],
    },
    "https://www.pacopacomama.com/dyn/phpauto/movie_details/movie_id/053026_100.json": {
        "Title": "Paco Title",
        "ActressesJa": "Actor P",
        "Desc": "Paco outline",
        "Duration": 1640,
        "Release": "2026/05/30",
        "Series": "Series P",
        "UCNAME": "Pacopacomama",
        "ThumbHigh": "https://www.pacopacomama.com/moviepages/053026_100/images/l_hd.jpg",
    },
    "https://www.10musume.com/dyn/phpauto/movie_details/movie_id/060226_01.json": {
        "Title": "10Musume Title",
        "Actor": "Actor 10",
        "Desc": "10Musume outline",
        "Duration": 4710,
        "Release": "2026.06.02",
        "Series": "Series 10",
        "UCNAME": "10Musume",
        "ThumbHigh": "https://www.10musume.com/moviepages/060226_01/images/str.jpg",
    },
}


def _input(number: str) -> CrawlerInput:
    return CrawlerInput(
        appoint_number="",
        appoint_url="",
        file_path=None,
        mosaic="",
        number=number,
        short_number=number,
        language=Language.JP,
        org_language=Language.JP,
    )


@pytest.mark.asyncio
async def test_official_crawler_uses_prefix_mapping_and_dynamic_source():
    crawler = OfficialCrawler(client=FakeOfficialClient())
    res = await crawler.run(
        CrawlerInput(
            appoint_number="",
            appoint_url="",
            file_path=None,
            mosaic="",
            number="SSIS-001",
            short_number="SSIS-001",
            language=Language.JP,
            org_language=Language.JP,
        )
    )

    assert res.debug_info.error is None
    assert res.data is not None
    assert res.data.source == "s1s1s1"
    assert res.data.number == "SSIS-001"
    assert res.data.title == "Official Title"
    assert res.data.actors == ["Actor A"]
    assert res.data.outline == "Official outline"
    assert res.data.release == "2026-04-03"
    assert res.data.year == "2026"
    assert res.data.runtime == "120"
    assert res.data.series == "Series A"
    assert res.data.directors == ["Director A"]
    assert res.data.tags == ["Genre A"]
    assert res.data.publisher == "Label A"
    assert res.data.studio == "Studio A"
    assert res.data.thumb == "https://example.test/cover.jpg"
    assert res.data.poster == "https://example.test/poster.jpg"
    assert res.data.extrafanart == ["https://example.test/extra.jpg"]
    assert res.data.trailer == "https://example.test/trailer.mp4"


@pytest.mark.parametrize(
    ("number", "expected_site"),
    [
        ("060326-001", "caribbeancom"),
        ("053126_001", "1pondo"),
        ("053026_100", "pacopacomama"),
        ("060226_01", "10musume"),
        ("HEYZO-3850", "heyzo"),
        ("HEYZO3850", "heyzo"),
        ("carib060326-001", "caribbeancom"),
        ("1pon053126_001", "1pondo"),
        ("paco053026_100", "pacopacomama"),
        ("10mu060226_01", "10musume"),
    ],
)
def test_uncensored_official_route_rules(number, expected_site):
    assert route_uncensored_official(number) == expected_site


@pytest.mark.asyncio
async def test_official_crawler_scrapes_caribbeancom_uncensored_detail():
    client = FakeUncensoredOfficialClient()
    crawler = OfficialCrawler(client=client)

    res = await crawler.run(_input("060326-001"))

    assert res.debug_info.error is None
    assert res.data is not None
    assert res.data.source == "caribbeancom"
    assert res.data.title == "Caribbean Title"
    assert res.data.actors == ["Actor A", "Actor B"]
    assert res.data.release == "2026-06-03"
    assert res.data.runtime == "61"
    assert res.data.tags == ["Tag A", "Tag B"]
    assert res.data.thumb == "https://www.caribbeancom.com/moviepages/060326-001/images/l_l.jpg"
    assert res.data.trailer == "https://smovie.caribbeancom.com/sample/movies/060326-001/sample.mp4"
    assert res.data.external_id == "https://www.caribbeancom.com/moviepages/060326-001/index.html"
    assert client.calls[0][1]["encoding"] == "euc-jp"


@pytest.mark.asyncio
async def test_official_crawler_scrapes_heyzo_uncensored_detail():
    crawler = OfficialCrawler(client=FakeUncensoredOfficialClient())

    res = await crawler.run(_input("HEYZO-3850"))

    assert res.debug_info.error is None
    assert res.data is not None
    assert res.data.source == "heyzo"
    assert res.data.number == "HEYZO-3850"
    assert res.data.title == "HEYZO Title"
    assert res.data.actors == ["Actor H"]
    assert res.data.release == "2026-05-19"
    assert res.data.runtime == "61"
    assert res.data.thumb == "https://www.heyzo.com/contents/3000/3850/images/player_thumbnail.jpg"
    assert res.data.trailer == "https://sample.heyzo.com/contents/3000/3850/sample.mp4"


@pytest.mark.parametrize(
    ("number", "expected_source", "expected_title", "expected_runtime", "expected_release"),
    [
        ("053126_001", "1pondo", "1Pondo Title", "61", "2026-05-31"),
        ("053026_100", "pacopacomama", "Paco Title", "27", "2026-05-30"),
        ("060226_01", "10musume", "10Musume Title", "78", "2026-06-02"),
    ],
)
@pytest.mark.asyncio
async def test_official_crawler_scrapes_vue_uncensored_json_sites(
    number, expected_source, expected_title, expected_runtime, expected_release
):
    crawler = OfficialCrawler(client=FakeUncensoredOfficialClient())

    res = await crawler.run(_input(number))

    assert res.debug_info.error is None
    assert res.data is not None
    assert res.data.source == expected_source
    assert res.data.title == expected_title
    assert res.data.runtime == expected_runtime
    assert res.data.release == expected_release
    assert res.data.external_id.startswith(f"https://www.{expected_source}")


def test_official_crawler_is_registered():
    assert get_crawler(Website.OFFICIAL) is OfficialCrawler
