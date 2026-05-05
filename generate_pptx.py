import re
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt
import textwrap

# ── Colour palette ──────────────────────────────────────────────────────────
BG_DARK       = RGBColor(0x0F, 0x17, 0x2A)   # deep navy
BG_SECTION    = RGBColor(0x1A, 0x26, 0x40)   # slightly lighter navy
ACCENT        = RGBColor(0x00, 0xB4, 0xD8)   # cyan
ACCENT2       = RGBColor(0x90, 0xE0, 0xEF)   # light cyan
TITLE_COLOR   = RGBColor(0xFF, 0xFF, 0xFF)   # white
BODY_COLOR    = RGBColor(0xE0, 0xE8, 0xF0)   # near-white
SUB_COLOR     = RGBColor(0xA0, 0xC4, 0xD8)   # muted cyan
NOTE_COLOR    = RGBColor(0x70, 0x90, 0xA8)   # dim for visual suggestions
SECTION_TEXT  = RGBColor(0x00, 0xB4, 0xD8)   # cyan for section headers

SLIDE_W = Inches(13.33)
SLIDE_H = Inches(7.5)

prs = Presentation()
prs.slide_width  = SLIDE_W
prs.slide_height = SLIDE_H

blank_layout = prs.slide_layouts[6]  # completely blank


def add_rect(slide, left, top, width, height, fill_rgb, transparency=0):
    shape = slide.shapes.add_shape(
        1,  # MSO_SHAPE_TYPE.RECTANGLE
        Inches(left), Inches(top), Inches(width), Inches(height)
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill_rgb
    shape.line.fill.background()
    return shape


def add_textbox(slide, left, top, width, height):
    return slide.shapes.add_textbox(
        Inches(left), Inches(top), Inches(width), Inches(height)
    )


def set_run(run, text, bold=False, italic=False, size=18, color=BODY_COLOR):
    run.text = text
    run.font.bold  = bold
    run.font.italic = italic
    run.font.size  = Pt(size)
    run.font.color.rgb = color


def make_title_slide(prs, title="System Design: Complete Guide", subtitle="Based on the System Design Primer"):
    slide = prs.slides.add_slide(blank_layout)
    # background
    add_rect(slide, 0, 0, 13.33, 7.5, BG_DARK)
    # accent bar left
    add_rect(slide, 0, 0, 0.08, 7.5, ACCENT)
    # accent bar bottom
    add_rect(slide, 0, 6.8, 13.33, 0.08, ACCENT)

    tb = add_textbox(slide, 0.5, 1.8, 12.3, 1.5)
    p = tb.text_frame.paragraphs[0]
    p.alignment = PP_ALIGN.LEFT
    run = p.add_run()
    set_run(run, title, bold=True, size=44, color=TITLE_COLOR)

    tb2 = add_textbox(slide, 0.5, 3.5, 12.3, 0.8)
    p2 = tb2.text_frame.paragraphs[0]
    p2.alignment = PP_ALIGN.LEFT
    run2 = p2.add_run()
    set_run(run2, subtitle, size=22, color=ACCENT2)

    tb3 = add_textbox(slide, 0.5, 6.2, 12.3, 0.5)
    p3 = tb3.text_frame.paragraphs[0]
    p3.alignment = PP_ALIGN.LEFT
    run3 = p3.add_run()
    set_run(run3, "418 Slides  ·  11 Sections  ·  Fundamentals → Advanced", size=14, color=NOTE_COLOR)


def make_section_divider(prs, section_title):
    slide = prs.slides.add_slide(blank_layout)
    add_rect(slide, 0, 0, 13.33, 7.5, BG_SECTION)
    add_rect(slide, 0, 0, 0.12, 7.5, ACCENT)
    add_rect(slide, 0.12, 3.4, 13.21, 0.06, ACCENT)

    tb = add_textbox(slide, 0.5, 2.5, 12.5, 1.2)
    p = tb.text_frame.paragraphs[0]
    p.alignment = PP_ALIGN.LEFT
    run = p.add_run()
    set_run(run, section_title, bold=True, size=36, color=SECTION_TEXT)


def make_content_slide(prs, title, bullets, visual_note=""):
    """
    bullets: list of (text, is_sub) tuples
    """
    slide = prs.slides.add_slide(blank_layout)
    # background
    add_rect(slide, 0, 0, 13.33, 7.5, BG_DARK)
    # top accent bar
    add_rect(slide, 0, 0, 13.33, 0.08, ACCENT)
    # title background strip
    add_rect(slide, 0, 0.08, 13.33, 1.05, RGBColor(0x15, 0x20, 0x38))
    # left accent
    add_rect(slide, 0, 0.08, 0.06, 1.05, ACCENT)

    # Title
    tb_title = add_textbox(slide, 0.25, 0.12, 12.8, 0.95)
    tf = tb_title.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.LEFT
    run = p.add_run()
    set_run(run, title, bold=True, size=24, color=TITLE_COLOR)

    # Body
    tb_body = add_textbox(slide, 0.35, 1.3, 12.6, 5.8)
    tf2 = tb_body.text_frame
    tf2.word_wrap = True

    first = True
    for (text, is_sub) in bullets:
        if first:
            p2 = tf2.paragraphs[0]
            first = False
        else:
            p2 = tf2.add_paragraph()

        if is_sub:
            p2.level = 1
            p2.alignment = PP_ALIGN.LEFT
            run2 = p2.add_run()
            # sub-bullet: show as "↳ text"
            set_run(run2, "    ↳  " + text, size=15, color=SUB_COLOR, italic=True)
        else:
            p2.level = 0
            p2.alignment = PP_ALIGN.LEFT
            run2 = p2.add_run()
            # bullet marker
            set_run(run2, "▸  " + text, size=17, color=BODY_COLOR)

        # paragraph spacing
        from pptx.oxml.ns import qn
        from lxml import etree
        pPr = p2._p.get_or_add_pPr()
        spcBef = etree.SubElement(pPr, qn('a:spcBef'))
        spcPts = etree.SubElement(spcBef, qn('a:spcPts'))
        spcPts.set('val', '140' if is_sub else '200')

    # Visual note at bottom (if any)
    if visual_note:
        tb_note = add_textbox(slide, 0.35, 6.85, 12.6, 0.55)
        tf3 = tb_note.text_frame
        p3 = tf3.paragraphs[0]
        p3.alignment = PP_ALIGN.LEFT
        run3 = p3.add_run()
        # truncate long notes
        note_text = visual_note if len(visual_note) <= 130 else visual_note[:127] + "..."
        set_run(run3, "📊 " + note_text, size=11, color=NOTE_COLOR, italic=True)

    return slide


# ── Parser ───────────────────────────────────────────────────────────────────

def parse_slides(md_text):
    """
    Returns list of dicts:
      {type: 'title'|'section'|'content', title, bullets, visual_note}
    """
    results = []
    lines = md_text.split('\n')
    i = 0

    current_slide = None

    def flush():
        if current_slide:
            results.append(current_slide)

    while i < len(lines):
        line = lines[i]

        # Section header  (## Section ...)
        if re.match(r'^## ', line):
            flush()
            current_slide = None
            sec_title = line[3:].strip()
            results.append({'type': 'section', 'title': sec_title})
            i += 1
            continue

        # Slide header  (### Slide N: Title)
        m = re.match(r'^### Slide \d+[:\-–]\s*(.*)', line)
        if m:
            flush()
            current_slide = {
                'type': 'content',
                'title': m.group(1).strip(),
                'bullets': [],
                'visual_note': ''
            }
            i += 1
            continue

        # Visual suggestion line
        if current_slide and re.match(r'^\[Visual suggestion', line, re.IGNORECASE):
            note = re.sub(r'^\[Visual suggestion[:\s]*', '', line, flags=re.IGNORECASE)
            note = note.rstrip(']').strip()
            current_slide['visual_note'] = note
            i += 1
            continue

        # Sub-bullet (4-space or 2-space indent + -)
        if current_slide and re.match(r'^[ \t]{2,}- ', line):
            text = re.sub(r'^[ \t]+-\s*', '', line).strip()
            if text:
                current_slide['bullets'].append((text, True))
            i += 1
            continue

        # Top-level bullet
        if current_slide and re.match(r'^- ', line):
            text = line[2:].strip()
            if text:
                current_slide['bullets'].append((text, False))
            i += 1
            continue

        i += 1

    flush()
    return results


# ── Main ─────────────────────────────────────────────────────────────────────

print("Reading slides markdown...")
with open('system-design-slides.md', 'r', encoding='utf-8') as f:
    md = f.read()

print("Parsing...")
slides_data = parse_slides(md)

print(f"Parsed {len(slides_data)} items")

# Cover slide
make_title_slide(prs)

content_count = 0
section_count = 0

for item in slides_data:
    if item['type'] == 'section':
        make_section_divider(prs, item['title'])
        section_count += 1
    elif item['type'] == 'content':
        make_content_slide(prs, item['title'], item['bullets'], item['visual_note'])
        content_count += 1

print(f"Generated: 1 cover + {section_count} section dividers + {content_count} content slides")
print(f"Total slides in PPTX: {len(prs.slides)}")

out = 'system-design-slides.pptx'
prs.save(out)
print(f"Saved → {out}")
