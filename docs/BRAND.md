# Brand

**Version:** 2 (2026-10-04)

v2 records the variants that now exist: the dark wordmark and the light "Aw" mark (as favicon exports). The monochrome wordmark and a dark mark do not exist yet. Colors and rules are unchanged.

How the Afterword name and logo are presented, so that future sessions, contributors, and the author do not improvise with them.

## Concept

The logo marks the point where publishing ends and conversation begins.

The wordmark treats its two halves differently, on purpose:

- **After** is upright, heavy, and dark. It represents the published artifact: the article, post, or piece of work that has reached a nominally finished state.
- **word** is italic, lighter, and blue. It represents what happens afterward: comments, questions, challenges, corrections, discussion, and the ideas that emerge because something was published.

The contrast between the halves is the idea. Anything that removes it, such as setting both halves the same way, removes the meaning.

## Meaning is carried by posture first

The primary distinction is **upright versus italic**. Color reinforces it but never carries it alone. This keeps the logo meaningful in monochrome, in print, and for viewers who do not distinguish the two colors.

## Colors

| Role | Name | Hex | Used for |
| --- | --- | --- | --- |
| The published artifact | Ink | `#111111` | "After" on light backgrounds |
| The conversation | Afterword Blue | `#477AA3` | "word" on light backgrounds |
| Dark-mode artifact | Paper | `#F2F2F2` | "After" on dark backgrounds (proposed) |
| Dark-mode conversation | Afterword Blue, light | `#6B9BC3` | "word" on dark backgrounds (proposed) |

Contrast, measured against WCAG 2 relative luminance:

- `#477AA3` on white is about 4.5:1.
- `#477AA3` on GitHub's dark background (`#0D1117`) is about 4.2:1, which reads as dim. The proposed `#6B9BC3` is about 6.4:1 on the same background.
- `#111111` on a dark background is effectively invisible, which is why a dark variant is required.

The two dark-mode values are proposals until the dark variant is drawn and approved. When approved, remove "(proposed)" and bump this document's version.

## Typography

The wordmark is artwork, not live text. Use the source files; never re-typeset the logo from a font, since spacing, weight, and the join between "r" and "w" are part of the design.

The typeface family and weights used in the source artwork are recorded alongside the source files in `img/`.

## Variants

| Variant | File | Use |
| --- | --- | --- |
| Wordmark, color, light backgrounds | `img/Afterword_logo_color.png` | Default |
| Wordmark, color, dark backgrounds | `img/Afterword_logo_color_dark.png` | Dark themes, including GitHub dark mode (wired into the README `<picture>`) |
| Wordmark, monochrome | `img/Afterword_logo_mono.png` (to be created) | Print, single-color contexts; both halves in one color, posture preserved |
| Mark, "Aw", light | `img/favicon-16x16.png`, `img/favicon-32x32.png`, `img/favicon.ico`, `img/apple-touch-icon.png` (180), `img/android-chrome-192x192.png`, `img/android-chrome-512x512.png`, `img/site.webmanifest` | Favicon, avatars, app icons, anything below the wordmark's minimum size. The 16 and 32 pixel PNGs are inlined as the label UI's favicon. Exported under favicon-generator names rather than `img/Afterword_mark.png`; no master file or SVG is in `img/` yet |
| Mark, "Aw", dark | (to be created) | Dark backgrounds |

Prefer SVG versions of each when they exist; PNG is the fallback.

### The "Aw" mark

A bold upright **A** followed by an italic **w**, in the same two colors and with the same posture contrast as the wordmark. It carries the full concept at small sizes: the finished artifact, then the conversation.

- Use the mark instead of the wordmark below the wordmark's minimum size.
- Provide light and dark versions, as for the wordmark.
- Export at 16, 32, 48, 180 (Apple touch icon), 192, and 512 pixels square, and check the 16 and 32 pixel versions by eye: the italic "w" must remain distinguishable from an upright one.

## Usage rules

- **Minimum size:** the wordmark is at least 120 pixels wide on screen. Below that, use the "Aw" mark.
- **Clear space:** keep empty space around the logo at least equal to the height of the lowercase "w" on every side.
- **Do not** set both halves upright, both italic, or both the same color.
- **Do not** swap the colors between the halves.
- **Do not** stretch, outline, rotate, add shadows, or place the logo on busy images.
- **Do not** substitute a different blue. Use the hex values above.
- **Alt text** for the logo is "Afterword".

## The name in prose

In running text, write **Afterword**: one word, capital A only, no styling. Not "AfterWord", "After Word", or "afterword" (except when referring to the ordinary noun). The two-part styling belongs to the logo, not the name.

## Using the logo in the README

Serve the light or dark variant automatically according to the viewer's theme:

```html
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="img/Afterword_logo_color_dark.png">
  <img alt="Afterword" src="img/Afterword_logo_color.png" width="360">
</picture>
```

The dark variant exists (2026-10-04), and the README uses this markup.

## Change control

Changes to colors, variants, or rules update this document and bump its version. Logo artwork changes are recorded with the date and the reason, like any other design decision in this project.