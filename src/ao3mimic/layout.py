from __future__ import annotations

import operator
import typing as T

import htpy as h

from . import __version__ as code_version
from .models import Category, Chapter, Series, Site, Work, WorkInSeries, WorkWarning
from .utils import clean_userstuff, comma_separated, thousands

if T.TYPE_CHECKING:
    import collections.abc as C

    from .render import Router


class Layout:
    def __init__(self, site: Site, router: Router):
        self.site = site
        self.router = router

    def site_skin(self, page_title: str, body, extra_header=None):
        if not (self.site.settings.single_work or page_title == self.site.settings.name):
            page_title += f" [{self.site.settings.name}]"
        if self.site.settings.single_work:
            nav_header_items = h.li[h.a]
        else:
            nav_header_items = [h.li[h.a(href=self.router.section_index("works"))["Works"]]]
            if self.site.series:
                nav_header_items.append(h.li[h.a(href=self.router.section_index("series"))["Series"]])
            nav_header_items.append(
                h.li(".search")[
                    h.form("#search.search", role="search", aria_label="Work", action="", accept_charset="UTF-8", method="get")[
                        h.fieldset[
                            h.p[
                                h.label(".landmark", for_="site_search")["Work Search"],
                                h.input(
                                    "#site_search.text",
                                    aria_describedby="site_search_tooltip",
                                    type="text",
                                    name="work_search[query]",
                                ),
                                h.span("#site_search_tooltip.tip", role="tooltip")["tip: words:100"],
                                h.span(".submit.actions")[h.input(".button", type="submit", value="Search", disabled=True)],
                            ]
                        ]
                    ]
                ]
            )
        about = None
        if self.site.settings.about:
            about = h.li(".module.group")[h.h4(".heading")["About"], h.ul(".menu")[h.li[self.site.settings.about]]]
        site_css = None
        if self.site.has_site_css:
            site_css = h.link(rel="stylesheet", type="text/css", media="screen", href=self.router.static_file("site.css"))
        return h.html(lang="en")[
            h.head[
                h.meta(charset="utf-8"),
                h.meta(http_equiv="x-ua-compatible", content="ie=edge"),
                h.meta(name="language", content="en-US"),
                h.meta(name="viewport", content="width=device-width, initial-scale=1.0"),
                h.title[page_title],
                h.link(rel="stylesheet", type="text/css", media="screen", href=self.router.static_file("styles.css")),
                site_css,
                h.script(src=self.router.static_file("_hyperscript-0.9.13.js"), type="text/javascript"),
                extra_header,
            ],
            h.body[
                h.div("#outer.wrapper")[
                    h.ul("#skiplinks")[h.li[h.a(href="#main")["Main Content"]]],
                    h.noscript[
                        h.p("#javascript-warning")[
                            "While we've done our best to make the core functionality of this site accessible without JavaScript, it will work better with it enabled. Please consider turning it on!"
                        ]
                    ],
                    h.header("#header.region")[
                        h.h1(".heading")[
                            h.a(href=self.router.root())[
                                h.span[self.site.settings.name],
                                h.sup[self.site.settings.release_status],
                                h.img(".logo", alt=self.site.settings.name, src=self.router.static_file("logo.png")),
                            ]
                        ],
                        h.nav(aria_label="Site")[h.ul(".primary.navigation.actions")[nav_header_items]],
                        h.div(".clear"),
                    ],
                    h.div("#inner.wrapper")[body],
                    h.div("#footer.region", role="contentinfo")[
                        h.h3(".landmark.heading")["Footer"],
                        h.ul(".navigation.actions", role="navigation")[
                            h.li(".module.group")[
                                h.h4(".heading")["Development"],
                                h.ul(".menu")[
                                    h.li[
                                        h.a(href=f"https://github.com/inklesspen/ao3mimic/commits/v{code_version}")[
                                            f"ao3mimic v{code_version}"
                                        ]
                                    ],
                                    h.li[
                                        h.a(title="View License", href="https://www.gnu.org/licenses/old-licenses/gpl-2.0.html")[
                                            "GPL-2.0-or-later"
                                        ]
                                    ],
                                ],
                            ],
                            about,
                        ],
                    ],
                ]
            ],
        ]

    def tag(self, tag):
        return h.a(".tag", rel="noreferrer", href=tag[1])[tag[0]] if isinstance(tag, tuple) else h.span(".tag")[tag]

    def warning_symbol(self, warnings: C.Sequence[WorkWarning]):
        if len(warnings) == 0:
            warnings_el = h.li[
                h.a(".help.symbol.question", title="Symbols key")[
                    h.span(".warning-choosenotto.warnings", title="Choose Not To Use Archive Warnings")[
                        h.span(".text")["Choose Not To Use Archive Warnings"]
                    ]
                ]
            ]
        elif warnings == [WorkWarning.NOT_APPLICABLE]:
            warnings_el = h.li[
                h.a(".help.symbol.question", title="Symbols key")[
                    h.span(".warning-no.warnings", title="No Archive Warnings Apply")[h.span(".text")["No Archive Warnings Apply"]]
                ]
            ]
        elif frozenset((WorkWarning.NOT_APPLICABLE, WorkWarning.CHOSE_NOT_TO_USE)).issuperset(warnings):
            warnings_el = h.li[
                h.a(".help.symbol.question", title="Symbols key")[
                    h.span(".warning-choosenotto.warnings", title="Choose Not To Use Archive Warnings")[
                        h.span(".text")["Choose Not To Use Archive Warnings"]
                    ]
                ]
            ]
        else:
            warning_text = ", ".join(frozenset([str(w) for w in warnings]))
            warnings_el = h.li[
                h.a(".help.symbol.question", title="Symbols key")[
                    h.span(".warning-yes.warnings", title=warning_text)[h.span(".text")[warning_text]]
                ]
            ]
        return warnings_el

    def categories_symbol(self, categories: C.Sequence[Category]):
        if len(categories) == 0:
            category_class = "none"
            category_text = "No category"
        elif len(categories) == 1:
            category_class = categories[0].css_class
            category_text = categories[0].value
        else:
            category_class = "multi"
            category_text = ", ".join(frozenset([str(w) for w in categories]))
        return h.li[
            h.a(".help.symbol.question", title="Symbols key")[
                h.span(class_=[category_class, "category"], title=category_text)[h.span(".text")[category_text]]
            ]
        ]

    def complete_wip_symbol(self, is_complete: bool):
        return (
            h.li[
                h.a(".help.symbol.question", title="Symbols key")[
                    h.span(".complete-yes.iswip", title="Complete Work")[h.span(".text")["Complete Work"]]
                ]
            ]
            if is_complete
            else h.li[
                h.a(".help.symbol.question", title="Symbols key")[
                    h.span(".complete-no.iswip", title="Work in Progress")[h.span(".text")["Work in Progress"]]
                ]
            ]
        )

    def work_blurb(self, work: Work):
        series = None
        wises = self.site.work_in_series.get(work.slug, [])
        if wises:
            series = [
                h.h6(".landmark.heading")["Series"],
                h.ul(".series")[
                    (
                        h.li[
                            "Part ",
                            h.strong[wis.position],
                            " of ",
                            h.a(href=self.router.series_detail(wis.series))[wis.series.title],
                        ]
                        for wis in wises
                    )
                ],
            ]
        return (
            h.li(".work.blurb.group", role="article")[
                h.div(".header.module")[
                    h.h4(".heading")[h.a(href=self.router.first_chapter_path(work))[work.title], f" by {work.author}"],
                    h.h5(".fandoms.heading")[
                        h.span(".landmark")["Fandoms:"], comma_separated((self.tag(fandom) for fandom in work.fandoms))
                    ],
                    h.ul(".required-tags")[
                        h.li[
                            h.a(".help.symbol.question", title="Symbols key")[
                                h.span(class_=[work.rating.css_class, "rating"], title=work.rating.value)[
                                    h.span(".text")[work.rating.value]
                                ]
                            ]
                        ],
                        self.warning_symbol(work.warnings),
                        self.categories_symbol(work.categories),
                        self.complete_wip_symbol(work.is_complete),
                    ],
                    h.p(".datetime")[work.published],
                ],
                h.h6(".landmark.heading")["Tags"],
                h.ul(".tags.commas")[
                    (h.li(".warnings")[h.strong[self.tag(warning.value)]] for warning in work.warnings),
                    (h.li(".relationships")[self.tag(relationship)] for relationship in work.relationships),
                    (h.li(".characters")[self.tag(character)] for character in work.characters),
                    (h.li(".freeforms")[self.tag(freeform)] for freeform in work.additional_tags),
                ],
                work.summary and [h.h6(".landmark.heading")["Summary"], h.blockquote(".userstuff.summary")[clean_userstuff(work.summary)]],
                series,
                h.dl(".stats")[
                    h.dt(".language")["Language:"],
                    h.dd(".language", lang="en")["English"],
                    h.dt(".words")["Words:"],
                    h.dd(".words")[thousands(work.wordcount)],
                    h.dt(".chapters")["Chapters:"],
                    h.dd(".chapters")[f"{work.chapter_count}/{work.total_chapter_count}"],
                ],
            ],
        )

    def series_blurb(self, series: Series):
        highest_rating = series.overall_rating
        rating_text = ", ".join(str(r) for r in series.ratings)
        rating = h.li[
            h.a(".help.symbol.question", title="Symbols key")[
                h.span(class_=[highest_rating.css_class, "rating"], title=rating_text)[h.span(".text")[rating_text]]
            ]
        ]
        return h.li(".series.blurb.group", role="article")[
            h.div(".header.module")[
                h.h4(".heading")[h.a(href=self.router.series_detail(series))[series.title]],
                h.ul(".required-tags")[
                    rating,
                    self.warning_symbol(series.warnings),
                    self.categories_symbol(series.categories),
                    self.complete_wip_symbol(all(work.is_complete for work in series.works)),
                ],
            ],
            series.summary and [h.h6(".landmark.heading")["Summary"], h.blockquote(".userstuff.summary")[clean_userstuff(series.summary)]],
            h.dl(".stats")[
                h.dt["Words:"],
                h.dd[thousands(sum([work.wordcount for work in series.works]))],
                h.dt["Works:"],
                h.dd[len(series.works)],
            ],
        ]

    def _index(self, show_works: bool, show_series: bool):
        groups = []
        if show_works:
            groups.append(
                h.div("#works.work.listbox.group")[
                    h.h3(".heading")["Works"],
                    h.ul(".index.group")[(self.work_blurb(work) for work in self.site.works),],
                ]
            )
        if show_series:
            groups.append(
                h.div("#series.series.listbox.group")[
                    h.h3(".heading")["Series"],
                    h.ul(".index.group")[(self.series_blurb(series) for series in self.site.series),],
                ]
            )
        return self.site_skin(page_title=self.site.settings.name, body=h.div("#main.works-show.region", role="main")[groups])

    def archive_index(self):
        return self._index(show_works=True, show_series=True)

    def series_index(self):
        return self._index(show_works=False, show_series=True)

    def works_index(self):
        return self._index(show_works=True, show_series=False)

    def series_detail(self, series: Series):
        header_items = []
        if series.summary:
            header_items.append(h.dt["Description:"])
            header_items.append(h.dd[h.blockquote(".userstuff")[clean_userstuff(series.summary)]])
        if series.notes:
            header_items.append(h.dt["Notes:"])
            header_items.append(h.dd[h.blockquote(".userstuff")[clean_userstuff(series.notes)]])

        body = h.div("#main.series-show.region", role="main")[
            h.div(".flash"),
            h.h2(".heading")[series.title],
            h.h3(".landmark.heading")["Series Metadata"],
            h.div(".wrapper")[
                h.dl(".series.meta.group")[
                    header_items,
                    h.dt(".stats")["Stats:"],
                    h.dd(".stats")[
                        h.dl(".stats")[
                            h.dt(".words")["Words:"],
                            h.dd(".words")[thousands(sum([work.wordcount for work in series.works]))],
                            h.dt(".works")["Works:"],
                            h.dd(".works")[len(series.works)],
                        ]
                    ],
                ]
            ],
            h.h3(".landmark.heading")["Listing Series"],
            h.ul(".series.work.index.group")[(self.work_blurb(work) for work in series.works),],
            h.div(".clear"),
        ]
        return self.site_skin(page_title=series.title, body=body)

    def work_index(self, work: Work):
        body = h.div("#main.works-show.region", role="main")[h.div("#works.work.group")[h.ul(".index.group")[self.work_blurb(work)]]]
        return self.site_skin(page_title=f"{work.title} - {work.author}", body=body)

    def _chapter_display_title(self, work: Work, chapter: Chapter):
        if work.display_chapter_numbers and work.display_num_for_chapter(chapter) is not None:
            return f"{work.display_num_for_chapter(chapter)}. {chapter.title}"
        return chapter.title

    def work_nav(self, work: Work):
        body = h.div("#main.works-navigate.region", role="main")[
            h.h2(".heading")["Chapter Index for ", h.a(href=self.router.first_chapter_path(work))[work.title]],
            h.ol(".chapter.index.group", role="navigation")[
                (
                    h.li[h.a(href=self.router.chapter_path(work, chapter))[self._chapter_display_title(work, chapter)]]
                    for chapter in work.chapters
                )
            ],
        ]
        return self.site_skin(page_title=f"{work.title} - {work.author}", body=body)

    def _chapter_option(self, work: Work, chapter: Chapter, current_chapter: Chapter):
        return h.option(selected=(chapter is current_chapter), value=self.router.chapter_path(work, chapter))[
            self._chapter_display_title(work, chapter)
        ]

    def _series_links(self, wis: WorkInSeries):
        items = []
        if wis.backward is not None:
            items.extend(
                (h.a(".previous", href=self.router.first_chapter_path(wis.backward.work))["← Previous Work"], h.span(".divider")[" "])
            )
        items.append(
            h.span(".position")[
                f"Part {wis.position} of ",
                h.a(href=self.router.series_detail(wis.series))[wis.series.title],
            ]
        )
        if wis.forward is not None:
            items.extend((h.span(".divider")[" "], h.a(".next", href=self.router.first_chapter_path(wis.forward.work))["Next Work →"]))
        return h.span(".series")[items]

    def _work_chapters(
        self, work: Work, chapters: C.Sequence[Chapter], is_all_chapters: bool, show_preface: bool, show_afterward: bool, page_title: str
    ):
        extra_header = None
        if work.has_work_css:
            extra_header = h.link(rel="stylesheet", type="text/css", media="screen", href=self.router.work_stylesheet(work))

        nav_items = []
        if is_all_chapters and not work.is_oneshot:
            nav_items.append(h.li(".chapter.bychapter")[h.a(href=self.router.first_chapter_path(work))["Chapter by Chapter"]])
        if not work.is_oneshot and not is_all_chapters:
            nav_items.append(h.li(".chapter.entire")[h.a(href=self.router.entire_work_path(work))["Entire Work"]])
            current_chapter = chapters[0]
            previous_chapter = work.previous_chapter(current_chapter)
            next_chapter = work.next_chapter(current_chapter)
            if previous_chapter is not None:
                nav_items.append(
                    h.li(".chapter.previous")[h.a(href=self.router.chapter_path(work, previous_chapter))["← Previous Chapter"]]
                )
            if next_chapter is not None:
                nav_items.append(h.li(".chapter.next")[h.a(href=self.router.chapter_path(work, next_chapter))["Next Chapter →"]])
            nav_items.append(
                h.li(".chapter", aria_haspopup="true")[
                    h.noscript[h.a(href=self.router.work_nav_path(work))["Chapter Index"]],
                    h.button(
                        ".collapsed.hidden",
                        {
                            "_": "init remove .hidden from me end on click toggle between .collapsed and .expanded on me then toggle .hidden on the next <ul/>"
                        },
                    )["Chapter Index"],
                    h.ul("#chapter_index.expandable.secondary.hidden")[
                        h.li[
                            h.p[
                                h.select("#selected_id", {"name": "selected_id", "_": "on change go to url `${my value}`"})[
                                    (self._chapter_option(work, chapter, current_chapter) for chapter in work.chapters)
                                ]
                            ]
                        ],
                        h.li[h.a(href=self.router.work_nav_path(work))["Full-page index"]],
                    ],
                ]
            )
        if work.download_link:
            nav_items.append(h.li(".download")[h.a(ref="noreferrer", href=work.download_link)["Download"]])

        categories = None
        if work.categories:
            categories = [
                h.dt(".category.tags")["Category:" if len(work.categories) == 1 else "Categories:"],
                h.dd(".category.tags")[h.ul(".commas")[(h.li[category.value] for category in work.categories)]],
            ]
        fandoms = None
        if work.fandoms:
            fandoms = [
                h.dt(".fandom.tags")["Fandom:" if len(work.fandoms) == 1 else "Fandoms:"],
                h.dd(".fandom.tags")[h.ul(".commas")[(h.li[self.tag(tag)] for tag in work.fandoms)]],
            ]
        relationships = None
        if work.relationships:
            relationships = [
                h.dt(".relationship.tags")["Relationship:" if len(work.relationships) == 1 else "Relationships:"],
                h.dd(".relationship.tags")[h.ul(".commas")[(h.li[self.tag(tag)] for tag in work.relationships)]],
            ]
        characters = None
        if work.characters:
            characters = [
                h.dt(".character.tags")["Character:" if len(work.characters) == 1 else "Characters:"],
                h.dd(".character.tags")[h.ul(".commas")[(h.li[self.tag(tag)] for tag in work.characters)]],
            ]
        freeforms = None
        if work.additional_tags:
            freeforms = [
                h.dt(".freeform.tags")["Additional Tags:"],
                h.dd(".freeform.tags")[h.ul(".commas")[h.ul(".commas")[(h.li[self.tag(tag)] for tag in work.additional_tags)]]],
            ]
        series = None
        wises = self.site.work_in_series.get(work.slug, [])
        wises.sort(key=operator.attrgetter("series.sort_key"))
        if wises:
            series = [h.dt(".series")["Series:"], h.dd(".series")[comma_separated((self._series_links(wis) for wis in wises))]]
        collections = None
        if work.collections:
            collections = [
                h.dt(".collections")["Collections:"],
                h.dd(".collections")[
                    comma_separated((h.a(ref="noreferrer", href=collection[1])[collection[0]] for collection in work.collections))
                ],
            ]

        metadata = h.dl(".work.meta.group")[
            h.dt(".rating.tags")["Rating:"],
            h.dd(".rating.tags")[h.ul(".commas")[h.li[self.tag(work.rating.value)]]],
            h.dt(".warning.tags")["Archive Warning:" if len(work.warnings) == 1 else "Archive Warnings:"],
            h.dd(".warning.tags")[h.ul(".commas")[(h.li[self.tag(warning.value)] for warning in work.warnings)]],
            categories,
            fandoms,
            relationships,
            characters,
            freeforms,
            series,
            collections,
            h.dt(".stats")["Stats:"],
            h.dd(".stats")[
                h.dl(".stats")[
                    h.dt(".published")["Published:"],
                    h.dd(".published")[work.published],
                    h.dt(".words")["Words:"],
                    h.dd(".words")[thousands(work.wordcount)],
                    h.dt(".chapters")["Chapters:"],
                    h.dd(".chapters")[f"{work.chapter_count}/{work.total_chapter_count}"],
                ]
            ],
        ]
        preface = None
        if show_preface:
            preface = []
            if work.summary is not None:
                preface.append(
                    h.div(".summary.module")[h.h3(".heading")["Summary:"], h.blockquote(".userstuff")[clean_userstuff(work.summary)]]
                )
            if work.notes_before is not None:
                preface.append(
                    h.div(".notes.module")[h.h3(".heading")["Notes:"], h.blockquote(".userstuff")[clean_userstuff(work.notes_before)]]
                )
        chapterstuff = []
        if work.is_oneshot:
            chapterstuff.append(h.h3("#work.landmark.heading")["Work Text:"])
            chapterstuff.append(h.div(".userstuff")[clean_userstuff(work.chapters[0].content)])
        else:
            for chapter in chapters:
                titleprefix = []
                if work.display_chapter_numbers and work.display_num_for_chapter(chapter) is not None:
                    titleprefix.extend(("Chapter ", work.display_num_for_chapter(chapter), " — "))
                chapter_preface = [
                    h.h3(".title")[
                        titleprefix,
                        h.a(href=self.router.chapter_path(work, chapter))[chapter.title],
                    ]
                ]
                if chapter.summary is not None:
                    chapter_preface.append(
                        h.div("#summary.summary.module")[
                            h.h3(".heading")["Summary:"], h.blockquote(".userstuff")[clean_userstuff(chapter.summary)]
                        ]
                    )
                if chapter.notes_before is not None:
                    chapter_preface.append(
                        h.div("#notes.notes.module")[
                            h.h3(".heading")["Notes:"], h.blockquote(".userstuff")[clean_userstuff(chapter.notes_before)]
                        ]
                    )
                chapter_afterward = None
                if chapter.notes_after is not None:
                    chapter_afterward = h.div(".chapter.preface.group")[
                        h.div("#chapter-${chapter.num}-endnotes.end.notes.module", role="complementary")[
                            h.h3(".heading")["Notes:"], h.blockquote(".userstuff")[clean_userstuff(chapter.notes_after)]
                        ]
                    ]
                chapterstuff.append(
                    h.div(".chapter", {"id": f"chapter-{chapter.num}"})[
                        h.div(".chapter.preface.group", role="complementary")[
                            chapter_preface,
                            h.div(".userstuff.module", role="article")[
                                h.h3("#work.landmark.heading")["Chapter Text"], clean_userstuff(chapter.content)
                            ],
                            chapter_afterward,
                        ],
                    ]
                )
        afterward = None
        if show_afterward and (work.notes_after or series):
            afterward_items = []
            if work.notes_after is not None:
                afterward_items.append(
                    h.div("#work_endnotes.end.notes.module")[
                        h.h3(".heading")["Notes:"], h.blockquote(".userstuff")[clean_userstuff(work.notes_after)]
                    ]
                )
            if wises:
                afterward_items.append(
                    h.div("#series.series.module")[
                        h.h3(".heading")["Series this work belongs to:"], h.ul[h.li[(self._series_links(wis) for wis in wises)]]
                    ]
                )
            afterward = h.div(".afterword.preface.group")[afterward_items]
        bottom_nav = [h.li[h.a(href="#main")["↑ Top"]]]
        if not work.is_oneshot and not is_all_chapters:
            if previous_chapter is not None:
                bottom_nav.append(
                    h.li(".chapter.previous")[h.a(href=self.router.chapter_path(work, previous_chapter))["← Previous Chapter"]]
                )
            if next_chapter is not None:
                bottom_nav.append(h.li(".chapter.next")[h.a(href=self.router.chapter_path(work, next_chapter))["Next Chapter →"]])

        body = h.div("#main.chapters-show.region", role="main")[
            h.div(".flash"),
            h.div(".work")[
                h.p(".landmark")[h.a(name="top")],
                h.h3(".landmark.heading")["Actions"],
                h.ul(".work.navigation.actions", role="menu")[nav_items],
                h.h3(".landmark.heading")["Work Header"],
                h.div(".wrapper")[metadata],
                h.div("#workskin")[
                    h.div(".preface.group")[
                        h.h2(".title.heading")[work.title],
                        h.h3(".byline.heading")[work.author],
                        preface,
                    ],
                    h.div("#chapters", role="main")[chapterstuff,],
                    afterward,
                ],
            ],
            h.div[
                h.h3(".landmark.heading")["Actions"],
                h.ul(".actions", role="navigation")[bottom_nav],
            ],
            h.div(".clear"),
        ]
        return self.site_skin(page_title=page_title, body=body, extra_header=extra_header)

    def work_allchapters(self, work: Work):
        return self._work_chapters(
            work,
            chapters=work.chapters,
            is_all_chapters=True,
            show_preface=True,
            show_afterward=True,
            page_title=f"{work.title} - {work.author}",
        )

    def work_chapter(self, work: Work, chapter: Chapter):
        show_preface = chapter is work.chapters[0]
        show_afterward = chapter is work.chapters[-1]
        return self._work_chapters(
            work,
            chapters=[chapter],
            is_all_chapters=False,
            show_preface=show_preface,
            show_afterward=show_afterward,
            page_title=f"{work.title} - {chapter.title} - {work.author}",
        )
