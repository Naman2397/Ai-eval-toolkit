# Visual QA checklist

Run `pptx_qa.py` first for the mechanical checks, then do this human pass on
a full render (export to PDF or present mode — thumbnails lie).

## Layout
- [ ] No text overflowing its shape or running off the slide
- [ ] No overlapping titles, labels, or figures
- [ ] Tables and charts fit their containers; nothing cramped to the point of illegibility
- [ ] Consistent spacing and alignment across slides

## Readability
- [ ] Text contrast sufficient against backgrounds
- [ ] Chart labels legible at presentation distance
- [ ] Long titles wrap cleanly instead of colliding with content

## Template match
- [ ] Color palette follows the style reference
- [ ] Typography (families, sizes, hierarchy) follows the reference
- [ ] Required chrome present on every slide: logo, page numbers, footers

## Polish
- [ ] No placeholder, lorem ipsum, or "click to add" text
- [ ] No broken image icons or missing assets
- [ ] No leftover notes-to-self in speaker notes or slide text

## Scoring guide
- One overflow on a key slide, or one cramped chart: minor limitation.
- Defects on multiple slides affecting readability: partially successful.
- Layout broken across the deck: not successful.
