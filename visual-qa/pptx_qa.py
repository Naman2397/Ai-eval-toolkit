#!/usr/bin/env python3
"""
pptx_qa.py — mechanical quality checks for a generated PowerPoint deck.

Automates the countable parts of visual QA so the human pass can focus on
taste: slide count, fonts, overflow heuristics, placeholders, and media.

Usage:
  python pptx_qa.py --deck your_deck.pptx --expected-slides 10

Heuristics are approximate — always render the deck and do a human pass
before finalizing a verdict (see visual-qa-checklist.md).
"""

import argparse
import sys
from pathlib import Path

try:
    from pptx import Presentation
    from pptx.enum.shapes import MSO_SHAPE_TYPE
except ImportError:
    print("python-pptx is required: pip install python-pptx", file=sys.stderr)
    sys.exit(2)


PLACEHOLDER_PHRASES = [
    "lorem ipsum", "insert text", "click to add", "todo", "tbd",
    "[insert", "sample text", "placeholder",
]

# Rough heuristic: characters that typically fit per square inch at ~18pt.
CHARS_PER_SQIN_AT_18PT = 90


def emu_to_inches(emu: int) -> float:
    return emu / 914400


def shape_text_overflow(shape) -> bool:
    """Heuristic: text far longer than the shape's area suggests overflow."""
    if not shape.has_text_frame:
        return False
    text = shape.text.strip()
    if not text:
        return False
    try:
        area_sqin = emu_to_inches(shape.width) * emu_to_inches(shape.height)
    except Exception:
        return False
    if area_sqin <= 0:
        return len(text) > 20
    # Scale capacity by area relative to the 18pt baseline.
    capacity = CHARS_PER_SQIN_AT_18PT * area_sqin
    return len(text) > capacity * 2.5


def audit(deck_path: Path, expected_slides: int | None) -> int:
    prs = Presentation(str(deck_path))
    slides = list(prs.slides)
    issues: list[str] = []
    notes: list[str] = []

    # Slide count
    if expected_slides is not None and len(slides) != expected_slides:
        issues.append(
            f"Slide count is {len(slides)}, expected {expected_slides}."
        )
    else:
        notes.append(f"Slide count: {len(slides)}" +
                     (f" (matches expected {expected_slides})" if expected_slides else ""))

    # Fonts used
    fonts: set[str] = set()
    for slide in slides:
        for shape in slide.shapes:
            if shape.has_text_frame:
                for para in shape.text_frame.paragraphs:
                    for run in para.runs:
                        if run.font.name:
                            fonts.add(run.font.name)
    notes.append(f"Fonts used: {', '.join(sorted(fonts)) if fonts else 'none detected'}")
    if len(fonts) > 3:
        issues.append(f"More than 3 fonts in use ({len(fonts)}) — check template match.")

    # Per-slide checks
    for i, slide in enumerate(slides, start=1):
        texts = []
        images = 0
        tables = 0
        for shape in slide.shapes:
            if shape.has_text_frame:
                t = shape.text.strip()
                if t:
                    texts.append(t)
                if shape_text_overflow(shape):
                    issues.append(f"Slide {i}: possible text overflow "
                                  f"({len(t)} chars in a small shape).")
            if shape.shape_type == MSO_SHAPE_TYPE.PICTURE:
                images += 1
            if shape.has_table:
                tables += 1
        full_text = "\n".join(texts).lower()
        for phrase in PLACEHOLDER_PHRASES:
            if phrase in full_text:
                issues.append(f"Slide {i}: possible placeholder text ('{phrase}').")
                break
        if not texts and images == 0 and tables == 0:
            issues.append(f"Slide {i}: appears empty (no text, images, or tables).")
        notes.append(f"Slide {i}: {len(texts)} text shapes, {images} images, {tables} tables")

    # Slide size / aspect
    w_in, h_in = emu_to_inches(prs.slide_width), emu_to_inches(prs.slide_height)
    notes.append(f"Slide size: {w_in:.2f} x {h_in:.2f} in")

    print(f"Deck: {deck_path.name}")
    for note in notes:
        print(f"  {note}")
    if not issues:
        print("Result: PASS — no mechanical issues found. Human render pass still required.")
        return 0
    print(f"Result: {len(issues)} issue(s) to review:")
    for issue in issues:
        print(f"  - {issue}")
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Mechanical QA checks for a PowerPoint deck.")
    parser.add_argument("--deck", required=True, type=Path)
    parser.add_argument("--expected-slides", type=int, default=None)
    args = parser.parse_args()
    if not args.deck.exists():
        print(f"Deck not found: {args.deck}", file=sys.stderr)
        return 2
    return audit(args.deck, args.expected_slides)


if __name__ == "__main__":
    sys.exit(main())
