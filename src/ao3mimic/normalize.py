import pathlib

import bs4
import tomli_w
from msgspec import Struct

from .models import Work
from .utils import resolve_tag


class NormalizeArgs(Struct):
    work: pathlib.Path
    dry_run: bool
    skip_tag_check: bool


def remove_nulls(d: dict):
    keys = list(d.keys())
    for key in keys:
        if d[key] is None:
            del d[key]


def normalize_work(work: Work, check_tag_existence=False):
    missing = []
    for chapter in work.chapters:
        if not chapter.content_path.is_file():
            missing.append(chapter)
    if missing:
        raise ValueError(f"Some chapter files for {work.slug} are missing!")
    for i, tag in enumerate(work.fandoms):
        work.fandoms[i] = resolve_tag(tag, check_existence=check_tag_existence)
    for i, tag in enumerate(work.relationships):
        work.relationships[i] = resolve_tag(tag, is_ship=True, check_existence=check_tag_existence)
    for i, tag in enumerate(work.characters):
        work.characters[i] = resolve_tag(tag, check_existence=check_tag_existence)
    for i, tag in enumerate(work.additional_tags):
        work.additional_tags[i] = resolve_tag(tag, check_existence=check_tag_existence)
    for html_attr in ("summary", "notes_before", "notes_after"):
        value = getattr(work, html_attr)
        if value is None:
            continue
        soup = bs4.BeautifulSoup(value, "html5lib")
        if not all(isinstance(c, bs4.element.Tag) or c.strip() == "" for c in soup.body.contents):
            setattr(work, html_attr, f"<p>{value}</p>")


def normalize(args: NormalizeArgs):
    work_path = args.work.resolve()
    work = Work.load(work_path)
    normalize_work(work, check_tag_existence=not args.skip_tag_check)

    work_dict = work.asdict()
    remove_nulls(work_dict)
    for chapter_dict in work_dict["chapters"]:
        remove_nulls(chapter_dict)
        del chapter_dict["num"]

    if args.dry_run:
        print(tomli_w.dumps(work_dict, indent=2))
    else:
        tomli_w.dump(work_dict, work_path.open("wb"), indent=2)
