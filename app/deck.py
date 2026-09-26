"""PPTX deck generation using python-pptx.

Creates a professionally styled 3-5 slide PowerPoint presentation
with Marsh branding (deep navy blue + accent colors).
"""

import os
import logging
from datetime import datetime
from typing import Optional

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

from app.models import PitchDeck, SlideContent

logger = logging.getLogger(__name__)

# ── Marsh Brand Colors ──────────────────────────────────────────
MARSH_NAVY = RGBColor(0x00, 0x1F, 0x5B)       # Deep navy primary
MARSH_BLUE = RGBColor(0x00, 0x52, 0xC2)        # Medium blue accent
MARSH_LIGHT_BLUE = RGBColor(0x41, 0x8F, 0xDE)  # Light blue
MARSH_TEAL = RGBColor(0x00, 0x96, 0x88)        # Teal accent
MARSH_WHITE = RGBColor(0xFF, 0xFF, 0xFF)
MARSH_LIGHT_GRAY = RGBColor(0xF0, 0xF2, 0xF5)
MARSH_DARK_GRAY = RGBColor(0x33, 0x33, 0x33)
MARSH_MEDIUM_GRAY = RGBColor(0x66, 0x66, 0x66)

# Slide dimensions (widescreen 16:9)
SLIDE_WIDTH = Inches(13.333)
SLIDE_HEIGHT = Inches(7.5)


def _add_background(slide, color=MARSH_NAVY):
    """Fill the slide background with a solid color."""
    background = slide.background
    fill = background.fill
    fill.solid()
    fill.fore_color.rgb = color


def _add_accent_bar(slide, left=0, top=0, width=Inches(13.333), height=Inches(0.08), color=MARSH_TEAL):
    """Add a thin accent bar to a slide."""
    shape = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, left, top, width, height
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = color
    shape.line.fill.background()


def _add_text_box(slide, left, top, width, height, text, font_size=18,
                  font_color=MARSH_WHITE, bold=False, alignment=PP_ALIGN.LEFT,
                  font_name="Calibri"):
    """Add a text box to a slide with specified styling."""
    txBox = slide.shapes.add_textbox(left, top, width, height)
    tf = txBox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = text
    p.font.size = Pt(font_size)
    p.font.color.rgb = font_color
    p.font.bold = bold
    p.font.name = font_name
    p.alignment = alignment
    return txBox


def _create_title_slide(prs, pitch: PitchDeck):
    """Create the title slide with Marsh branding."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # Blank layout
    _add_background(slide, MARSH_NAVY)
    
    # Top accent bar
    _add_accent_bar(slide, top=0, color=MARSH_TEAL)
    
    # Company name - large
    _add_text_box(
        slide,
        left=Inches(1), top=Inches(1.8),
        width=Inches(11), height=Inches(1.5),
        text=pitch.company_name,
        font_size=40, font_color=MARSH_WHITE, bold=True,
    )
    
    # Subtitle
    _add_text_box(
        slide,
        left=Inches(1), top=Inches(3.3),
        width=Inches(11), height=Inches(0.8),
        text="Medical Insurance — Tailored Coverage Proposal",
        font_size=22, font_color=MARSH_LIGHT_BLUE, bold=False,
    )
    
    # Bottom accent bar
    _add_accent_bar(slide, top=Inches(5.5), width=Inches(4), color=MARSH_TEAL)
    
    # Marsh branding
    _add_text_box(
        slide,
        left=Inches(1), top=Inches(6.2),
        width=Inches(6), height=Inches(0.5),
        text="Prepared by Marsh | " + datetime.now().strftime("%B %Y"),
        font_size=12, font_color=MARSH_MEDIUM_GRAY,
    )
    
    # "MARSH" wordmark
    _add_text_box(
        slide,
        left=Inches(9.5), top=Inches(6.2),
        width=Inches(3), height=Inches(0.6),
        text="MARSH",
        font_size=28, font_color=MARSH_BLUE, bold=True,
        alignment=PP_ALIGN.RIGHT,
    )


def _create_content_slide(prs, slide_content: SlideContent):
    """Create a content slide with bullet points."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # Blank layout
    _add_background(slide, MARSH_WHITE)
    
    # Left accent bar
    shape = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, 0, 0, Inches(0.12), Inches(7.5)
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = MARSH_NAVY
    shape.line.fill.background()
    
    # Top accent line
    _add_accent_bar(slide, left=Inches(0.12), top=0, 
                    width=Inches(13.2), height=Inches(0.04), color=MARSH_TEAL)
    
    # Slide number
    _add_text_box(
        slide,
        left=Inches(0.4), top=Inches(0.3),
        width=Inches(1), height=Inches(0.5),
        text=f"0{slide_content.slide_number}",
        font_size=14, font_color=MARSH_TEAL, bold=True,
    )
    
    # Title
    _add_text_box(
        slide,
        left=Inches(0.8), top=Inches(0.6),
        width=Inches(11), height=Inches(0.9),
        text=slide_content.title,
        font_size=28, font_color=MARSH_NAVY, bold=True,
    )
    
    # Subtitle (if present)
    y_offset = Inches(1.5)
    if slide_content.subtitle:
        _add_text_box(
            slide,
            left=Inches(0.8), top=y_offset,
            width=Inches(11), height=Inches(0.5),
            text=slide_content.subtitle,
            font_size=16, font_color=MARSH_MEDIUM_GRAY,
        )
        y_offset = Inches(2.1)
    
    # Bullet points
    if slide_content.bullet_points:
        txBox = slide.shapes.add_textbox(
            Inches(0.8), y_offset,
            Inches(11.5), Inches(4.5)
        )
        tf = txBox.text_frame
        tf.word_wrap = True
        
        for i, point in enumerate(slide_content.bullet_points):
            if i == 0:
                p = tf.paragraphs[0]
            else:
                p = tf.add_paragraph()
            
            p.text = point
            p.font.size = Pt(16)
            p.font.color.rgb = MARSH_DARK_GRAY
            p.font.name = "Calibri"
            p.space_after = Pt(12)
            p.level = 0
            
            # Add bullet character
            p.text = "▸  " + point
    
    # Footer bar
    _add_accent_bar(slide, top=Inches(7.2), width=Inches(13.333), 
                    height=Inches(0.3), color=MARSH_NAVY)
    
    _add_text_box(
        slide,
        left=Inches(0.5), top=Inches(7.15),
        width=Inches(5), height=Inches(0.3),
        text="MARSH — Confidential",
        font_size=9, font_color=MARSH_WHITE,
    )


def _create_recommendation_slide(prs, pitch: PitchDeck):
    """Create the final recommendation slide."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # Blank layout
    _add_background(slide, MARSH_NAVY)
    
    # Top accent bar
    _add_accent_bar(slide, top=0, color=MARSH_TEAL)
    
    # "Our Recommendation" header
    _add_text_box(
        slide,
        left=Inches(1), top=Inches(0.8),
        width=Inches(11), height=Inches(0.6),
        text="OUR RECOMMENDATION",
        font_size=14, font_color=MARSH_TEAL, bold=True,
    )
    
    # Recommended policy name
    _add_text_box(
        slide,
        left=Inches(1), top=Inches(1.5),
        width=Inches(11), height=Inches(1.2),
        text=pitch.recommended_policy,
        font_size=36, font_color=MARSH_WHITE, bold=True,
    )
    
    # Rationale box
    rect = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE,
        Inches(1), Inches(3),
        Inches(11), Inches(2.5),
    )
    rect.fill.solid()
    rect.fill.fore_color.rgb = RGBColor(0x00, 0x2D, 0x72)  # Slightly lighter navy
    rect.line.fill.background()
    
    # Rationale text
    _add_text_box(
        slide,
        left=Inches(1.3), top=Inches(3.2),
        width=Inches(10.4), height=Inches(0.5),
        text="Why This Policy?",
        font_size=18, font_color=MARSH_TEAL, bold=True,
    )
    
    _add_text_box(
        slide,
        left=Inches(1.3), top=Inches(3.8),
        width=Inches(10.4), height=Inches(1.5),
        text=pitch.recommendation_rationale,
        font_size=16, font_color=MARSH_LIGHT_GRAY,
    )
    
    # Bottom bar
    _add_accent_bar(slide, top=Inches(6.5), width=Inches(3), color=MARSH_TEAL)
    
    # Contact CTA
    _add_text_box(
        slide,
        left=Inches(1), top=Inches(6.7),
        width=Inches(11), height=Inches(0.5),
        text="Contact your Marsh advisor to discuss this recommendation.",
        font_size=14, font_color=MARSH_MEDIUM_GRAY,
    )


def generate_deck(pitch: PitchDeck, output_dir: str) -> str:
    """Generate a .pptx file from a PitchDeck object.
    
    Args:
        pitch: The pitch deck content.
        output_dir: Directory to save the .pptx file.
        
    Returns:
        The filename of the generated deck.
    """
    logger.info(f"Generating PPTX deck for {pitch.company_name}")
    
    prs = Presentation()
    prs.slide_width = SLIDE_WIDTH
    prs.slide_height = SLIDE_HEIGHT
    
    # 1. Title slide
    _create_title_slide(prs, pitch)
    
    # 2. Content slides (skip last slide if it's the recommendation)
    for slide_content in pitch.slides:
        _create_content_slide(prs, slide_content)
    
    # 3. Recommendation slide
    _create_recommendation_slide(prs, pitch)
    
    # Save
    os.makedirs(output_dir, exist_ok=True)
    safe_name = "".join(c if c.isalnum() or c in " _-" else "_" for c in pitch.company_name)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"Marsh_Pitch_{safe_name}_{timestamp}.pptx"
    filepath = os.path.join(output_dir, filename)
    
    prs.save(filepath)
    logger.info(f"Deck saved to: {filepath}")
    
    return filename
