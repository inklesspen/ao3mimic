from __future__ import annotations

import importlib.resources
import pathlib
import shutil
import subprocess
import typing as T

from werkzeug.exceptions import NotFound
from werkzeug.routing import Map, Rule

from .layout import Layout
from .utils import format_chapter_number, get_css_site_urls, get_site_urls, make_relative_url, urlpath_to_filepath

if T.TYPE_CHECKING:
    import collections.abc as C

    from .models import Chapter, Series, Site, Work

REGULAR_URL_MAP = Map(
    [
        Rule("/", endpoint="archive.index"),
        Rule("/series/", endpoint="series.index"),
        Rule("/series/<slug>/", endpoint="series.detail"),
        Rule("/works/", endpoint="works.index"),
        Rule("/works/<slug>/", endpoint="work.index"),
        Rule("/works/<slug>/nav.html", endpoint="work.nav"),
        Rule("/works/<slug>/work.html", endpoint="work.all_chapters"),
        Rule("/works/<slug>/<chapter_number>.html", endpoint="work.chapter"),
        Rule("/works/<slug>/media/<filename>", endpoint="work.media"),
        Rule("/works/<slug>/work.css", endpoint="work.stylesheet"),
        Rule("/static/logo.png", endpoint="site.logo"),
        Rule("/static/styles.css", endpoint="archive.stylesheet"),
        Rule("/static/site.css", endpoint="site.stylesheet"),
        Rule("/static/<filename>", endpoint="static_file"),
    ]
)

SINGLE_WORK_URL_MAP = Map(
    [
        Rule("/", endpoint="work.index"),
        Rule("/nav.html", endpoint="work.nav"),
        Rule("/work.html", endpoint="work.all_chapters"),
        Rule("/<chapter_number>.html", endpoint="work.chapter"),
        Rule("/media/<filename>", endpoint="work.media"),
        Rule("/work.css", endpoint="work.stylesheet"),
        Rule("/static/logo.png", endpoint="site.logo"),
        Rule("/static/styles.css", endpoint="archive.stylesheet"),
        Rule("/static/site.css", endpoint="site.stylesheet"),
        Rule("/static/<filename>", endpoint="static_file"),
    ]
)

STYLESHEET_ENDPOINTS = frozenset(["work.stylesheet", "archive.stylesheet", "site.stylesheet"])
BINARY_ENDPOINTS = frozenset(["work.media", "work.stylesheet", "site.logo", "archive.stylesheet", "site.stylesheet", "static_file"])

type RouteArgs = C.Mapping[str, T.Any]


class Router:
    endpoint: str
    args: RouteArgs
    is_binary: bool

    def __init__(self, site: Site, url_map: Map, url: str):
        self.site = site
        self.current_url = url
        self.active_mapping = url_map.bind("archive.example", "/", path_info=url)
        try:
            endpoint, args = self.active_mapping.match()
        except NotFound:
            raise KeyError(url) from None
        self.endpoint = endpoint
        self.args = args
        self.is_binary = endpoint in BINARY_ENDPOINTS

    def _build_relative(self, endpoint: str, **values):
        if self.site.settings.single_work and "slug" in values:
            actual_slug = values.pop("slug")
            expected_slug = self.site.works[0].slug
            assert actual_slug == expected_slug
        return make_relative_url(from_url=self.active_mapping.path_info, to_url=self.active_mapping.build(endpoint, values))

    def root(self):
        endpoint = "work.index" if self.site.settings.single_work else "archive.index"
        return self._build_relative(endpoint)

    def section_index(self, section: str):
        if self.site.settings.single_work:
            raise ValueError("Can't have section indexes in single-work mode.")
        if section not in ["series", "works"]:
            raise ValueError("Bad section type")
        endpoint = f"{section}.index"
        return self._build_relative(endpoint)

    def static_file(self, filename: str):
        return self._build_relative("static_file", filename=filename)

    def first_chapter_path(self, work: Work):
        return self.chapter_path(work, work.chapters[0])

    def chapter_path(self, work: Work, chapter: Chapter):
        if work.is_oneshot:
            return self._build_relative("work.index", slug=work.slug)
        chapter_number = format_chapter_number(chapter.num, len(work.chapters))
        return self._build_relative("work.chapter", slug=work.slug, chapter_number=chapter_number)

    def entire_work_path(self, work: Work):
        endpoint = "work.index" if work.is_oneshot else "work.all_chapters"
        return self._build_relative(endpoint, slug=work.slug)

    def work_nav_path(self, work: Work):
        return self._build_relative("work.nav", slug=work.slug)

    def work_index_path(self, work: Work):
        return self._build_relative("work.index", slug=work.slug)

    def work_stylesheet(self, work: Work):
        if not work.has_work_css:
            raise ValueError("This work doesn't have a stylesheet.")
        return self._build_relative("work.stylesheet", slug=work.slug)

    def series_detail(self, series: Series):
        return self._build_relative("series.detail", slug=series.slug)


class RenderableArchive:
    def __init__(self, site: Site):
        self.site = site
        self.url_map = SINGLE_WORK_URL_MAP if self.site.settings.single_work else REGULAR_URL_MAP

    def render_layout(self, router: Router):
        layout = Layout(self.site, router)
        match router.endpoint:
            case "archive.index":
                return str(layout.archive_index())
            case "works.index":
                return str(layout.works_index())
            case "series.index":
                return str(layout.series_index())
            case "series.detail":
                series = self.site.get_series(router.args["slug"])
                return str(layout.series_detail(series))
            case "work.index":
                work = self.site.works[0] if self.site.settings.single_work else self.site.get_work(router.args["slug"])
                if work.is_oneshot:
                    return str(layout.work_allchapters(work))
                return str(layout.work_index(work))
            case "work.nav":
                work = self.site.works[0] if self.site.settings.single_work else self.site.get_work(router.args["slug"])
                return str(layout.work_nav(work))
            case "work.chapter":
                work = self.site.works[0] if self.site.settings.single_work else self.site.get_work(router.args["slug"])
                chapnum = int(router.args["chapter_number"])
                chapter = work.chapters[chapnum - 1]
                return str(layout.work_chapter(work, chapter))
            case "work.all_chapters":
                work = self.site.works[0] if self.site.settings.single_work else self.site.get_work(router.args["slug"])
                return str(layout.work_allchapters(work))
            case _:
                raise NotImplementedError(router.endpoint, router.args)

    def render_static_file(self, filename: str, dest_file: pathlib.Path):
        if not importlib.resources.is_resource("ao3mimic.static", filename):
            raise ValueError("Cannot find static file %s" % filename)
        with dest_file.open("wb") as dest:
            src = importlib.resources.open_binary("ao3mimic.static", filename)
            shutil.copyfileobj(src, dest)

    def render_logo(self, dest_file: pathlib.Path):
        with dest_file.open("wb") as dest:
            src = (
                self.site.settings.logo.open("rb")
                if self.site.settings.logo is not None
                else importlib.resources.open_binary("ao3mimic.branding", "not-ao3.png")
            )
            shutil.copyfileobj(src, dest)

    def render_sass(self, dest_file: pathlib.Path):
        sass = shutil.which("sass")
        with importlib.resources.as_file(importlib.resources.files("ao3mimic.branding") / "styles.scss") as scss_src:
            subprocess.check_call([sass, scss_src, dest_file])

    def render_work_media(self, work: Work, filename: str, dest_file: pathlib.Path):
        media_src = T.cast(pathlib.Path, work.work_path / "media")
        if not media_src.is_dir():
            raise ValueError("Work doesn't have media")
        media_file = media_src / filename
        if not media_file.is_file():
            raise ValueError("Requested media not found")
        shutil.copyfile(media_file, dest_file)

    def render_binary(self, endpoint: str, args: RouteArgs, dest_file: pathlib.Path):
        match endpoint:
            case "static_file":
                self.render_static_file(args["filename"], dest_file)
            case "site.logo":
                self.render_logo(dest_file)
            case "archive.stylesheet":
                self.render_sass(dest_file)
            case "site.stylesheet":
                shutil.copyfile(self.site.site_css, dest_file)
            case "work.media":
                work = self.site.works[0] if self.site.settings.single_work else self.site.get_work(args["slug"])
                self.render_work_media(work, args["filename"], dest_file)
            case "work.stylesheet":
                work = self.site.works[0] if self.site.settings.single_work else self.site.get_work(args["slug"])
                shutil.copyfile(work.work_css, dest_file)
            case _:
                raise NotImplementedError(endpoint, args)

    def render(self, output_directory: pathlib.Path):
        output_directory = output_directory.resolve()
        if output_directory.is_dir():
            shutil.rmtree(output_directory)
        output_directory.mkdir()

        # we start with the root, of course.
        to_render = {"/"}
        # the work indexes are never linked directly (except for oneshots) so let's get them too.
        if not self.site.settings.single_work:
            root_router = Router(self.site, self.url_map, "/")
            to_render.update("/" + root_router.work_index_path(work) for work in self.site.works)
        rendered = set()
        while to_render:
            current = to_render.pop()
            router = Router(self.site, self.url_map, current)
            rendered.add(current)
            dest_file = output_directory / urlpath_to_filepath(current)
            dest_file.parent.mkdir(parents=True, exist_ok=True)
            if router.is_binary:
                self.render_binary(router.endpoint, router.args, dest_file)
                if router.endpoint in STYLESHEET_ENDPOINTS:
                    to_render.update(get_css_site_urls(dest_file.read_text(), current))
            else:
                data = self.render_layout(router)
                to_render.update(get_site_urls(data, current))
                dest_file.write_text(data)
            to_render.difference_update(rendered)
