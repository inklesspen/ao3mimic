import htpy
import hyperlink
import pytest
from markupsafe import Markup

from ao3mimic.utils import clean_userstuff, comma_separated, make_relative_url


@pytest.mark.parametrize(
    "from_url,to_url,expected",
    [
        ("/", "/", "."),
        ("/", "/static/styles.css", "static/styles.css"),
        ("/", "/series/sherlock-holmes/", "series/sherlock-holmes/"),
        ("/series/sherlock-holmes/", "/works/a-scandal-in-bohemia/1.html", "../../works/a-scandal-in-bohemia/1.html"),
        ("/series/sherlock-holmes/", "/series/", ".."),
        ("/series/", "/static/styles.css", "../static/styles.css"),
        ("/works/dracula/", "/works/dracula/nav.html", "nav.html"),
        ("/works/dracula/01.html", "/works/dracula/nav.html", "nav.html"),
        ("/works/dracula/nav.html", "/works/dracula/", "."),
    ],
)
def test_make_relative_url(from_url, to_url, expected):
    assert (actual := make_relative_url(from_url, to_url)) == expected
    navigated = hyperlink.parse(from_url).click(actual)
    assert str(navigated) == to_url


@pytest.mark.parametrize(
    "elements,expected",
    [
        ([htpy.span(".example")["foo"]], '<span class="example">foo</span>'),
        (
            [htpy.span(".example")["foo"], htpy.span(".example")["bar"], htpy.span(".example")["baz"]],
            '<span class="example">foo</span>, <span class="example">bar</span>, <span class="example">baz</span>',
        ),
    ],
)
def test_comma_separated(elements, expected):
    assert htpy.render_node(comma_separated(elements)) == Markup(expected)


def test_clean_userstuff_preserves_all_items():
    html = '<p><a href="../static/styles.css">Foo</a></p><hr/><p><i>bar</i></p>'
    assert clean_userstuff(html) == Markup(html)


def test_clean_userstuff_adds_rel_attr_on_external_links():
    html = '<p><a href="http://example.com">Please buy my product</a></p>'
    expected = '<p><a href="http://example.com" rel="noreferrer">Please buy my product</a></p>'
    assert clean_userstuff(html) == Markup(expected)
