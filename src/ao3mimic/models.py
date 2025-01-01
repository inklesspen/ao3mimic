from __future__ import annotations

import datetime
import enum
import functools
import itertools
import pathlib
import typing as T

import cattrs
import msgspec
from msgspec import Struct

from .exceptions import SiteStructureError
from .utils import count_html_text, tomllib

converter = cattrs.Converter()
converter.register_unstructure_hook(
    Struct, functools.partial(msgspec.to_builtins, builtin_types=(datetime.date,), order="sorted", enc_hook=converter.unstructure)
)


def msgspec_dec_hook(type: T.Type, obj: T.Any):
    return converter.structure(obj, type)


converter.register_structure_hook(Struct, functools.partial(msgspec.convert, dec_hook=msgspec_dec_hook))


class Category(enum.Enum):
    GEN = "Gen"
    F_F = "F/F"
    F_M = "F/M"
    M_M = "M/M"
    MULTI = "Multi"
    OTHER = "Other"

    def __str__(self):
        return self.value

    @property
    def css_class(self):
        match self:
            case Category.GEN:
                return "category-gen"
            case Category.F_F:
                return "category-femslash"
            case Category.F_M:
                return "category-het"
            case Category.M_M:
                return "category-slash"
            case Category.MULTI:
                return "category-multi"
            case Category.OTHER:
                return "category-other"
        raise AssertionError()

    @property
    def sort_order(self):
        for i, e in enumerate(self.__class__):
            if e is self:
                return i
        raise AssertionError()

    def __ge__(self, other):
        if self.__class__ is other.__class__:
            return self.sort_order >= other.sort_order
        return NotImplemented

    def __gt__(self, other):
        if self.__class__ is other.__class__:
            return self.sort_order > other.sort_order
        return NotImplemented

    def __le__(self, other):
        if self.__class__ is other.__class__:
            return self.sort_order <= other.sort_order
        return NotImplemented

    def __lt__(self, other):
        if self.__class__ is other.__class__:
            return self.sort_order < other.sort_order
        return NotImplemented


class WorkWarning(enum.Enum):
    NOT_APPLICABLE = "No Archive Warnings Apply"
    CHOSE_NOT_TO_USE = "Choose Not To Use Archive Warnings"
    VIOLENCE = "Graphic Depictions Of Violence"
    DEATH = "Major Character Death"
    NONCON = "Rape/Non-Con"
    UNDERAGE = "Underage Sex"

    def __str__(self):
        return self.value


class Rating(enum.Enum):
    NOT_RATED = "Not Rated"
    GENERAL = "General Audiences"
    TEEN = "Teen And Up Audiences"
    MATURE = "Mature"
    EXPLICIT = "Explicit"

    def __str__(self):
        return self.value

    @property
    def css_class(self):
        match self:
            case Rating.NOT_RATED:
                return "rating-notrated"
            case Rating.GENERAL:
                return "rating-general-audience"
            case Rating.TEEN:
                return "rating-teen"
            case Rating.MATURE:
                return "rating-mature"
            case Rating.EXPLICIT:
                return "rating-explicit"
        raise AssertionError()

    @property
    def priority(self):
        for i, e in enumerate(self.__class__):
            if e is self:
                return i
        raise AssertionError()

    def __ge__(self, other):
        if self.__class__ is other.__class__:
            return self.priority >= other.priority
        return NotImplemented

    def __gt__(self, other):
        if self.__class__ is other.__class__:
            return self.priority > other.priority
        return NotImplemented

    def __le__(self, other):
        if self.__class__ is other.__class__:
            return self.priority <= other.priority
        return NotImplemented

    def __lt__(self, other):
        if self.__class__ is other.__class__:
            return self.priority < other.priority
        return NotImplemented


class DateGranularity(enum.Enum):
    DAY = "DAY"
    MONTH = "MONTH"
    YEAR = "YEAR"


class Settings(Struct, kw_only=True):
    name: str
    release_status: str = "alpha"
    logo: T.Optional[pathlib.Path] = None
    single_work: bool = False
    about: T.Optional[str] = None

    @classmethod
    def load(cls, toml_path: pathlib.Path):
        settings_dict = tomllib.load(toml_path.open("rb"))
        settings = converter.structure(settings_dict, Settings)
        if settings.logo is not None:
            logo_path = toml_path.parent / settings.logo
            if not logo_path.is_file():
                raise SiteStructureError("Logo path was specified, but the file cannot be found")
            settings.logo = logo_path
        return settings


class Work(Struct, kw_only=True, dict=True):
    slug: str
    ordering: int = 0
    title: str
    author: str
    rating: Rating
    warnings: list[WorkWarning]
    categories: list[Category]
    fandoms: list[tuple[str, str] | str]
    relationships: list[tuple[str, str] | str]
    characters: list[tuple[str, str] | str]
    additional_tags: list[tuple[str, str] | str]
    collections: list[tuple[str, str]] = []
    pubdate: datetime.date
    pubdate_granularity: DateGranularity = DateGranularity.DAY
    summary: T.Optional[str] = None
    notes_before: T.Optional[str] = None
    notes_after: T.Optional[str] = None
    download_link: T.Optional[str] = None
    is_complete: bool = True
    display_chapter_numbers: bool
    chapters: list[Chapter]

    @classmethod
    def load(cls, toml_path: pathlib.Path):
        work_dict = tomllib.load(toml_path.open("rb"))
        work_path = toml_path.parent.resolve()
        work_dict["slug"] = work_path.name

        if "chapters" not in work_dict and "content_file" in work_dict:
            chapter = {"title": "Oneshot", "content_file": work_dict.pop("content_file")}
            work_dict["chapters"] = [chapter]

        if "display_chapter_numbers" not in work_dict and len(work_dict["chapters"]) == 1:
            work_dict["display_chapter_numbers"] = False

        for num, chapter_dict in enumerate(work_dict["chapters"], start=1):
            chapter_dict["num"] = num

        work = converter.structure(work_dict, Work)
        work.work_path = work_path
        for chapter in work.chapters:
            chapter.work_path = work_path

        return work

    @property
    def sort_key(self):
        return (self.ordering, self.slug)

    def asdict(self) -> dict[str, T.Any]:
        work_dict = converter.unstructure(self)
        del work_dict["slug"]
        return work_dict

    @property
    def published(self):
        match self.pubdate_granularity:
            case DateGranularity.DAY:
                return self.pubdate.strftime("%Y-%m-%d")
            case DateGranularity.MONTH:
                return self.pubdate.strftime("%Y-%m")
            case DateGranularity.YEAR:
                return self.pubdate.strftime("%Y")
        raise AssertionError()

    @property
    def chapter_count(self):
        return len(self._substantial_chapters)

    @property
    def total_chapter_count(self):
        # TODO: move this into views
        return str(self.chapter_count) if self.is_complete else "?"

    @functools.cached_property
    def wordcount(self):
        return sum([c.wordcount for c in self.chapters])

    @property
    def is_oneshot(self):
        return len(self.chapters) == 1

    def next_chapter(self, chapter: Chapter):
        if chapter not in self.chapters:
            raise ValueError("Provided chapter is not one of this work's chapters")
        if chapter is self.chapters[-1]:
            # last chapter, no next chapter
            return None
        i = self.chapters.index(chapter)
        return self.chapters[i + 1]

    def previous_chapter(self, chapter: Chapter):
        if chapter not in self.chapters:
            raise ValueError("Provided chapter is not one of this work's chapters")
        if chapter is self.chapters[0]:
            # first chapter, no previous chapter
            return None
        i = self.chapters.index(chapter)
        return self.chapters[i - 1]

    @functools.cached_property
    def _substantial_chapters(self):
        return [c for c in self.chapters if not c.interstitial]

    def display_num_for_chapter(self, chapter: Chapter):
        if chapter.interstitial:
            return None
        return self._substantial_chapters.index(chapter) + 1

    @property
    def work_css(self):
        return T.cast(pathlib.Path, self.work_path) / "work.css"

    @property
    def has_work_css(self):
        return self.work_css.is_file()


class Chapter(Struct, kw_only=True, dict=True):
    num: int
    title: str
    interstitial: bool = False
    content_file: pathlib.Path
    summary: T.Optional[str] = None
    notes_before: T.Optional[str] = None
    notes_after: T.Optional[str] = None

    @functools.cached_property
    def content_path(self):
        return T.cast(pathlib.Path, self.work_path) / self.content_file

    @functools.cached_property
    def content(self):
        return self.content_path.read_text()

    @functools.cached_property
    def wordcount(self):
        return count_html_text(self.content_path.read_text())


class Series(Struct, kw_only=True):
    slug: str
    ordering: int = 0
    title: str
    summary: T.Optional[str] = None
    notes: T.Optional[str] = None
    works: list[Work]

    @classmethod
    def load(cls, toml_path: pathlib.Path, work_lookup: T.Mapping[str, Work]):
        series_dict = tomllib.load(toml_path.open("rb"))
        series_dict["slug"] = toml_path.stem

        work_slugs = series_dict.pop("works", [])
        series_dict["works"] = [work_lookup[slug] for slug in work_slugs]

        return converter.structure(series_dict, cls)

    @property
    def sort_key(self):
        return (self.ordering, self.slug)

    @property
    def ratings(self):
        return tuple(frozenset([work.rating for work in self.works]))

    @property
    def overall_rating(self):
        return max(self.ratings)

    @property
    def warnings(self):
        return tuple(frozenset(itertools.chain.from_iterable(work.warnings for work in self.works)))

    @property
    def categories(self):
        return tuple(frozenset(itertools.chain.from_iterable(work.categories for work in self.works)))


class WorkInSeries(Struct, kw_only=True):
    series: Series
    work: Work
    position: int
    backward: T.Optional[WorkInSeries] = None
    forward: T.Optional[WorkInSeries] = None


class Site(Struct, kw_only=True):
    base_path: pathlib.Path
    settings: Settings
    works: list[Work]
    series: list[Series]

    work_in_series: dict[str, list[WorkInSeries]]

    @classmethod
    def create(cls, base_path: pathlib.Path, settings: Settings, works: list[Work], series: list[Series]):
        if settings.single_work and len(works) != 1:
            raise SiteStructureError("single_work cannot be true if there is more than one work")
        if settings.single_work and len(series) != 0:
            raise SiteStructureError("single_work cannot be true if any series are defined")
        works.sort(key=lambda work: work.sort_key)
        series.sort(key=lambda series: series.sort_key)
        wises: dict[str, list[WorkInSeries]] = {}
        for s in series:
            s_wises: list[WorkInSeries] = []
            for i, w in enumerate(s.works, start=1):
                s_wises.append(WorkInSeries(series=s, work=w, position=i))
            for first, second in itertools.pairwise(s_wises):
                first.forward = second
                second.backward = first
            for wis in s_wises:
                wises.setdefault(wis.work.slug, []).append(wis)
        return cls(base_path=base_path, settings=settings, works=works, series=series, work_in_series=wises)

    @classmethod
    def load_single_work_site(cls, content_path: pathlib.Path, settings: Settings):
        work_toml = content_path / "work.toml"
        if not work_toml.is_file():
            raise SiteStructureError(
                "Expected to find a work.toml directory next to settings.toml (since single_work is true), but did not."
            )
        work = Work.load(work_toml)
        return cls.create(base_path=content_path, settings=settings, works=[work], series=[])

    @classmethod
    def load_site(cls, content_path: pathlib.Path):
        settings = Settings.load(content_path / "settings.toml")
        if settings.single_work:
            return cls.load_single_work_site(content_path, settings)
        works_path = content_path / "works"
        if not works_path.is_dir():
            raise SiteStructureError("Expected to find a works directory next to settings.toml, but did not.")
        works = [
            Work.load(work_path / "work.toml")
            for work_path in works_path.iterdir()
            if work_path.is_dir() and (work_path / "work.toml").is_file()
        ]
        series_path = content_path / "series"
        if series_path.is_dir():
            works_lookup = {work.slug: work for work in works}
            series = [
                Series.load(series_toml_path, works_lookup)
                for series_toml_path in series_path.iterdir()
                if series_toml_path.suffix == ".toml"
            ]
        else:
            series = []
        return cls.create(base_path=content_path, settings=settings, works=works, series=series)

    @property
    def site_css(self):
        return self.base_path / "site.css"

    @property
    def has_site_css(self):
        return self.site_css.is_file()

    def get_series(self, slug):
        series_lookup = {series.slug: series for series in self.series}
        return series_lookup[slug]

    def get_work(self, slug):
        works_lookup = {work.slug: work for work in self.works}
        return works_lookup[slug]
