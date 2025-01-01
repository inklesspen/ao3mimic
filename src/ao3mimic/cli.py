import argparse
import pathlib

from .models import Site, converter
from .normalize import NormalizeArgs, normalize
from .render import RenderableArchive

parser = argparse.ArgumentParser()
subparsers = parser.add_subparsers(dest="command", title="commands", required=True)

normalize_parser = subparsers.add_parser("normalize", help="Normalize a work's TOML file, including resolving tags.")
normalize_parser.add_argument("work", type=pathlib.Path, help="TOML file for the work")
normalize_parser.add_argument("--dry-run", action="store_true", help="Print out the normalized TOML instead of writing to the file")
normalize_parser.add_argument("--skip-tag-check", action="store_true", help="Don't check tag URLs against AO3")

analyze_parser = subparsers.add_parser("analyze", help="Analyze the content directory and print out various particulars.")
analyze_parser.add_argument("content", type=pathlib.Path, help="Directory with content")

render_parser = subparsers.add_parser("render", help="Render the site from the content directory")
render_parser.add_argument("content", type=pathlib.Path, help="Directory with content")
render_parser.add_argument("dest", type=pathlib.Path, help="Destination directory")


def display_site(site: Site):
    print(site.settings.name)
    if site.settings.about:
        print(site.settings.about)
    if site.settings.logo is not None:
        print(f"Site has custom logo: {site.settings.logo}")

    print()

    print("Works:")
    for work in site.works:
        print()
        print(f"{work.slug} — {work.title} — {work.author}")
        print(f"{work.rating} — {work.warnings} — {work.categories}")
        print(f"Fandoms: {[t[0] for t in work.fandoms]}")
        print(f"Relationships: {[t[0] for t in work.relationships]}")
        print(f"Characters: {[t[0] for t in work.characters]}")
        print(f"Additional Tags: {[t[0] for t in work.additional_tags]}")
        print(f"{work.published} — {work.chapter_count} chapters — {work.wordcount} words")
        if work.notes_before is not None:
            print("Has notes before")
        if work.notes_after is not None:
            print("Has notes after")
        if work.slug not in site.work_in_series:
            continue
        for wis in site.work_in_series[work.slug]:
            print(f"Series: {wis.position} in {wis.series.title}")


def main() -> None:
    args = vars(parser.parse_args())
    command = args.pop("command")
    if command == "normalize":
        normalize(converter.structure(args, NormalizeArgs))
    elif command == "analyze":
        display_site(Site.load_site(args["content"]))
    elif command == "render":
        site = Site.load_site(args["content"])
        archive = RenderableArchive(site)
        archive.render(args["dest"])
    else:
        raise AssertionError("This should never happen.")
