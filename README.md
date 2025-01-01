# ao3mimic

A friend of mine had difficulty focusing on reading books, but found it much easier to focus on reading stories on [AO3](https://archiveofourown.org/). So I built a tool to generate a static site mimicking the AO3 interface.

At the moment it is not particularly user-friendly, but you should be able to work out the necessary layout by looking in the sample-content directory.

## Basic instructions

Install the ao3mimic package in the usual way (uv, pipx, etc). I have only actually tested it with Python 3.12 but it may work with earlier versions.

Configure your content directory:

```
├── settings.toml
├── series
│   └── sherlock-holmes.toml
└── works
    ├── a-scandal-in-bohemia
    │   ├── part-1.html
    │   ├── part-2.html
    │   ├── part-3.html
    │   └── work.toml
    ├── the-adventure-of-the-blue-carbuncle
    │   ├── the-adventure-of-the-blue-carbuncle.html
    │   └── work.toml
    ├── the-adventure-of-the-dancing-men
    │   ├── media
    │   │   ├── e-letter.svg
    │   │   ├── illustration-1.svg
    │   │   ├── illustration-2.svg
    │   │   ├── illustration-3.svg
    │   │   ├── illustration-4.svg
    │   │   ├── illustration-5.svg
    │   │   ├── illustration-6.svg
    │   │   ├── n-letter.svg
    │   │   ├── r-letter.svg
    │   │   └── v-letter.svg
    │   ├── the-adventure-of-the-dancing-men.html
    │   ├── work.css
    │   └── work.toml
    ├── the-adventure-of-the-speckled-band
    │   ├── the-adventure-of-the-speckled-band.html
    │   └── work.toml
    └── the-redheaded-league
        ├── the-redheaded-league.html
        └── work.toml
```

Your content directory must contain a `settings.toml` file and a `works` directory; it can also contain a `series` directory, plus some other files which will be discussed later.

```toml
# settings.toml
name = "Site name"  # required
# AO3 still says it is in 'beta'. ao3mimic defaults to being in 'alpha', but you can change that with the optional release_status setting.
release_status = "pre-alpha"
# if present, the 'about' text will appear in the footer
about = "This is an about text."
# if you want to change the logo in the upper left, this should be a path to a 42 pixel high, 61 pixel wide PNG file.
logo = "my-logo.png"
```

Inside the `works` directory you should place at least one directory containing a "work"; a book or short story. The directory name will become the work's "slug". For example, in `works/a-scandal-in-bohemia`, the slug is `a-scandal-in-bohemia`.

Inside the work directory you should place HTML files containing the chapter(s), as well as a `work.toml` file.

```toml
# works/elfland/work.toml
# ordering defaults to 0, but you can set it to other numbers. Works are sorted first by their ordering value, then by their slug.
ordering = 2
# Most of these fields are required.
title = "The King of Elfland’s Daughter"
author = "Lord Dunsany"
# rating, warnings, and categories have specific sets of allowed values; see below.
rating = "Not Rated"
warnings = [
  "Choose Not To Use Archive Warnings",
]
categories = [
  "F/M",
]
# fandoms, relationshups, characters, and additional_tags are all "tag" fields. They can contain either a tag and link pair, or just a bare tag.
# it's okay to mix and match bare tags with linked tags within the same tag type.
# You can link to other sites besides AO3 also; consider Wikipedia articles, perhaps.
fandoms = [
  [
    "The King of Elfland’s Daughter - Lord Dunsany",
    "https://archiveofourown.org/tags/The%20King%20of%20Elfland%E2%80%99s%20Daughter%20-%20Lord%20Dunsany",
  ],
]
relationships = [
  "Alveric/Lirazel",
]
characters = [
  [
    "Alveric",
    "https://archiveofourown.org/tags/Alveric%20(Elfland)",
  ],
  [
    "Lirazel",
    "https://archiveofourown.org/tags/Lirazel%20(Elfland)",
  ],
  "Ziroonderel",
]
additional_tags = [
  [
    "Fae & Fairies",
    "https://archiveofourown.org/tags/Fae%20&%20Fairies",
  ],
]
# collections is optional, but collection entries must have links.
collections = [
  [
    "Fantasy Masterworks",
    "https://en.wikipedia.org/wiki/Fantasy_Masterworks",
  ],
]
# TOML syntax requires that the publication date have year, month, and day. However, you might not actually know which day a book was published on, so you can specify a YEAR or MONTH granularity.
pubdate = 1924-05-01
pubdate_granularity = "MONTH"  # optional; defaults to DAY.
# summary, notes_before, and notes_after are all optional. if present, they must be wrapped in <p>/<div>/etc tags.
summary = "<p>The people of the obscure village Erl demand to be ruled by a magic lord, so their ruler sends his son Alveric to Elfland to wed the elfin princess Lirazel. He brings her back to Erl and the couple have a son, but Lirazel has trouble integrating with human society. When a scheme by her father spirits her away and Elfland vanishes, Alveric begins a mad quest to find where Elfland went.</p>"
notes_before = "<p>I hope that no suggestion of any strange land that may be conveyed by the title will scare readers away from this book; for, though some chapters do indeed tell of Elfland, in the greater part of them there is no more to be shown than the face of the fields we know, and ordinary English woods and a common village and valley, a good twenty or twenty-five miles from the border of Elfland.</p>"
# if present, adds a Download button in the work header
download_link = "https://standardebooks.org/ebooks/lord-dunsany/the-king-of-elflands-daughter"
# is_complete defaults to true. if false, the total chapter count is replaced with "?"
is_complete = true
# You must set display_chapter_numbers to either true or false. If true, chapter titles are preceded with the number (as in, "Chapter 1 — Chapter Title").
# You might want to set this to false if the work doesn't actually have chapter titles, and thus the first chapter is titled "One", and so on.
display_chapter_numbers = true

# The chapters can be defined either with inline array and table syntax or "array of tables" syntax.
# "array of tables" is documented at https://toml.io/en/v1.0.0#array-of-tables
# If only one chapter is present, the work is considered a oneshot, and the chapter title (though still required) is ignored.
[[chapters]]
title = "The Plan of the Parliament of Erl"  # required
content_file = "chapter-01.html"  # required
interstitial = false  # optional
# if interstitial is true, the chapter is excluded from chapter numbering/counting. This is useful if a chapter is merely a book/part divider, or displays ancillary information such as a map.

[[chapters]]
title = "Alveric Comes in Sight of the Elfin Mountains"
content_file = "chapter-02.html"
interstitial = false

# for brevity's sake, we're skipping most of the chapters in this example; see elfland/work.toml for the full definition.

[[chapters]]
title = "The Last Great Rune"
content_file = "chapter-34.html"
interstitial = false
```

The legal values for rating, warnings, and categories are as follows:

```python
class Rating(enum.Enum):
    NOT_RATED = "Not Rated"
    GENERAL = "General Audiences"
    TEEN = "Teen And Up Audiences"
    MATURE = "Mature"
    EXPLICIT = "Explicit"

class WorkWarning(enum.Enum):
    NOT_APPLICABLE = "No Archive Warnings Apply"
    CHOSE_NOT_TO_USE = "Choose Not To Use Archive Warnings"
    VIOLENCE = "Graphic Depictions Of Violence"
    DEATH = "Major Character Death"
    NONCON = "Rape/Non-Con"
    UNDERAGE = "Underage Sex"

class Category(enum.Enum):
    GEN = "Gen"
    F_F = "F/F"
    F_M = "F/M"
    M_M = "M/M"
    MULTI = "Multi"
    OTHER = "Other"
```

There are two optional elements to a work directory: a work.css stylesheet and a media directory containing image files (or other media). See `the-adventure-of-the-dancing-men` for an example of both.

If you want to have series on your site as well, make a series directory containing toml files. The name of each toml file will be the series slug.

```toml
# series/fantasy-masterworks.toml
title = "Fantasy Masterworks"
ordering = 0  # optional; used for sorting in the same way that works are sorted
# summary and notes are both optional.
summary = "<p>Fantasy Masterworks is a series of British paperbacks by Millennium (an imprint of Victor Gollancz). It is intended to comprise “some of the greatest, most original, and most influential fantasy ever written” and to contain “the books which, along with Tolkien, Peake and others, shaped modern fantasy.”</p>"
notes = "<p>For a complete list of the books in the Fantasy Masterworks series, see <a href=\"https://en.wikipedia.org/wiki/Fantasy_Masterworks\">Wikipedia</a>.</p>"
# works in the series is given as a list of work slugs.
works = ["elfland"]
```

Finally, you can have site-wide css in a `site.css` file located adjacent to your `settings.toml`. If you would be using the same CSS styles in multiple `work.css` files, maybe put them in `site.css` instead.

Once you have configured your content directory, you can render it to HTML by running `ao3mimic render content/ output/`. Once rendered, you can upload it to a web server. Or, for testing purposes, you can run a local web server with `python -m http.server -d output`; it will start serving on port 8000 until you cancel it.

## Licensing and credits

The HTML and CSS for the rendered sites is derived from [otwarchive](https://github.com/otwcode/otwarchive/), which is licensed [GPL-2.0-or-later](https://www.gnu.org/licenses/gpl-2.0.html). Accordingly, ao3mimic is also licensed [GPL-2.0-or-later](https://www.gnu.org/licenses/gpl-2.0.html).

The books and stories in the sample-content directory were adapted from ebooks provided by [Standard Ebooks](https://standardebooks.org/).
