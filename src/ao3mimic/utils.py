from __future__ import annotations

import logging
import math
import posixpath
import typing as T

import bs4
import cssutils
import httpx
import hyperlink
import markupsafe
import more_itertools

try:
    import tomllib
except ImportError:
    import tomli as tomllib  # type: ignore  # noqa: F401

from ._wordchars import WORD_CHARS

if T.TYPE_CHECKING:
    import collections.abc as C

    import htpy


def count_html_text(html: str) -> int:
    soup = bs4.BeautifulSoup(html, "html5lib")
    return count_plain_text(soup.get_text())


def count_plain_text(text: str) -> int:
    return more_itertools.ilen(WORD_CHARS.finditer(text))


def thousands(num):
    return "{0:,d}".format(num)


TAG_URL_TEMPLATE = "https://archiveofourown.org/tags/{}"

timeout = httpx.Timeout(5.0, read=15.0)
client = httpx.Client(timeout=timeout)


def resolve_tag(tag: tuple[str, str] | str, is_ship=False, check_existence=False) -> tuple[str, str] | str:
    if isinstance(tag, str):
        if not check_existence:
            # Since we can't check against AO3, better to leave it as-is.
            return tag
        tag_text = tag
        tag_path = tag_text.replace(" & ", " *a* ").replace("&", " *a* ").replace("/", "*s*") if is_ship else tag_text
        tag = (tag_text, tag_path)
    tag_url = httpx.URL(tag[1])
    if tag_url.is_relative_url:
        tag_url = httpx.URL(TAG_URL_TEMPLATE.format(tag[1]))
        if check_existence:
            r = client.head(tag_url)
            if r.status_code != httpx.codes.OK:
                return tag[0]
    return (tag[0], str(tag_url))


def make_relative_url(from_url: str, to_url: str):
    assert from_url.startswith("/")
    assert to_url.startswith("/")
    # from_url needs to be a directory or else we get an extra level of '..', so strip any filename
    if filename := posixpath.basename(from_url):
        from_url = from_url.removesuffix(filename)
    assert from_url.endswith("/")
    relpath = posixpath.relpath(to_url, from_url)
    if to_url.endswith("/") and not relpath.endswith("."):
        relpath += "/"
    return relpath


def format_chapter_number(chapter_number: int, total_chapters: int):
    template_digits = math.floor(math.log10(total_chapters)) + 1
    return str(chapter_number).zfill(template_digits)


def comma_separated(values: C.Iterable[htpy.Element]) -> C.Iterator[htpy.Node]:
    return more_itertools.intersperse(", ", values)


def urlpath_to_filepath(path: str):
    assert path.startswith("/")
    if path.endswith("/"):
        path += "index.html"
    return path[1:]


def _css_null_fetcher(_):
    # disable
    return None, None


CSS_PARSER = cssutils.CSSParser(fetcher=_css_null_fetcher, loglevel=logging.CRITICAL)


def _site_urls(current_url: str, candidates: C.Iterable[str]):
    current_url = hyperlink.parse(current_url)
    for url in candidates:
        url = hyperlink.parse(url)
        if url.absolute or url.rooted or not url.path:
            continue
        yield str(current_url.click(url))


def get_css_site_urls(some_css: str, css_url: str) -> set[str]:
    sheet = CSS_PARSER.parseString(some_css, href=css_url)
    css_urls = set(cssutils.getUrls(sheet))
    return set(_site_urls(css_url, css_urls))


def get_site_urls(some_html: str, current_url: str) -> set[str]:
    soup = bs4.BeautifulSoup(some_html, "html5lib")
    hrefs = soup.find_all(href=True)
    srcs = soup.find_all(src=True)
    urls_in_page = set([tag["href"] for tag in hrefs] + [tag["src"] for tag in srcs])
    return set(_site_urls(current_url, urls_in_page))


def clean_userstuff(some_html: str):
    soup = bs4.BeautifulSoup(some_html, "html5lib")
    soup.head.decompose()
    for a_tag in soup.find_all("a", href=True):
        url = hyperlink.parse(a_tag["href"])
        if url.absolute:
            a_tag["rel"] = "noreferrer"
    soup.body.unwrap()
    soup.html.unwrap()
    return markupsafe.Markup(str(soup))
