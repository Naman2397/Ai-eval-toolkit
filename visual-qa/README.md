# Visual QA

Mechanical checks plus a human checklist for reviewing generated slide decks.

## Script

```bash
pip install python-pptx
python pptx_qa.py --deck your_deck.pptx --expected-slides 10
```

What it checks:
- slide count against the expected count
- fonts in use (flags more than 3 — usually a template mismatch)
- text-overflow heuristic per shape
- placeholder text ("lorem ipsum", "click to add", "TBD", …)
- empty slides, images and tables per slide, slide dimensions

## Checklist

`visual-qa-checklist.md` is the human pass: layout, readability, template
match, and polish, with a scoring guide. The script catches the mechanical
issues; the checklist catches taste. Always render before judging.
