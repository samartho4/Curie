# Curie — brand notes

Small, practical guide so the logo stays consistent wherever it's used.

## The mark
An open orbit with a single node — reads as a "C," an electron orbit (a nod to Curie's physics),
and a point tracked on a record. The node is the one accent; it repeats as the dot on the "i" in the
wordmark. Keep that teal node — it's the whole identity in one detail.

## Wordmark
Set in **Space Grotesk SemiBold**, tracking slightly tight. The logo files are outlined vectors, so
no font is required to display them. If you ever re-typeset "Curie," use Space Grotesk SemiBold.

## Palette
| Role | Hex | Notes |
|---|---|---|
| Ink | `#14161B` | wordmark, mark, body text |
| Radium Teal (accent) | `#14C3B0` | the node, the "i" dot, one highlight per layout |
| Paper | `#F6F6F3` | light background |
| Dark | `#0E0F13` | reversed background |
| Muted | `#6C7077` | tagline, secondary text |

Note: the accent is deliberately **not** red / amber / green, because the product uses those for
verdict status (collision / near-miss / clear). Brand color ≠ status color.

## Tagline
Primary: **No experiment starts blind.**
Descriptor (when you need to say what it is): *The lab's memory, in Slack.*

## Usage
- Keep clear space around the lockup equal to the height of the mark's node.
- Minimum width for the horizontal lockup: ~120px. Below that, use the icon.
- Use `logo-reversed` on dark backgrounds, `logo-mono` for single-color / print / stamping.
- Don't recolor the wordmark, stretch it, add effects, or drop the teal node.

## Files
- `logo-primary` — main horizontal lockup (mark + Curie)
- `logo-primary-tagline` — lockup with tagline
- `logo-stacked` — centered, mark over wordmark + tagline (square-ish spaces)
- `logo-reversed` — for dark backgrounds
- `logo-mono` — single ink color
- `wordmark` — type only
- `icon-light` / `icon-dark` / `icon-ink` — app icon / favicon tiles
- `arch-system` / `arch-flow` — architecture diagrams

Each is provided as `.svg` (source) and `.png` (2000px / 512px, ready to upload to Devpost).
