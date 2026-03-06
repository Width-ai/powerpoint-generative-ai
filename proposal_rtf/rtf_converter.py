"""
RTF converter that faithfully preserves original docx formatting.

Improvements over previous version:
- Reads actual font sizes from runs (not hardcoded)
- Reads actual font families from runs and document defaults
- Preserves inline formatting: bold, italic, underline, strikethrough, color per run
- Reads page/section properties: margins, page size, orientation
- Builds a proper RTF font table from all fonts found in the document
- Handles inline bold/italic/underline in markdown (not just whole-line)
"""

import io
import re
from typing import Union
from docx import Document
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _escape_rtf(text: str) -> str:
    """Escape special RTF characters and encode non-ASCII as Unicode escapes."""
    result = []
    for ch in text:
        if ch == '\\':
            result.append('\\\\')
        elif ch == '{':
            result.append('\\{')
        elif ch == '}':
            result.append('\\}')
        elif ch == '\r':
            pass
        elif ch == '\n':
            result.append('\\line\n')
        elif ord(ch) > 127:
            code = ord(ch)
            signed = code if code <= 32767 else code - 65536
            result.append(f'\\u{signed}?')
        else:
            result.append(ch)
    return ''.join(result)


def _half_points(size_obj) -> int:
    """Convert a docx font size to RTF half-points (fs unit).
    
    docx stores sizes in half-points already via the XML (sz element),
    but python-docx exposes them as Pt objects. RTF \\fs is also half-points.
    Returns a sensible default (24 = 12pt) when size is None.
    """
    if size_obj is None:
        return 24  # 12 pt default
    # python-docx Pt objects expose .pt
    try:
        return int(size_obj.pt * 2)
    except AttributeError:
        return 24


# ---------------------------------------------------------------------------
# Font table builder
# ---------------------------------------------------------------------------

class FontTable:
    """Collect all unique fonts used in a document and build an RTF font table."""

    def __init__(self):
        self._fonts: list[str] = []
        self._index: dict[str, int] = {}

    def register(self, name: str) -> int:
        """Register a font name and return its RTF index."""
        if not name:
            name = "Calibri"
        if name not in self._index:
            self._index[name] = len(self._fonts)
            self._fonts.append(name)
        return self._index[name]

    def get_index(self, name: str) -> int:
        return self._index.get(name or "Calibri", 0)

    def to_rtf(self) -> str:
        lines = ['{\\fonttbl\n']
        for i, name in enumerate(self._fonts):
            lines.append(f'{{\\f{i}\\fnil\\fcharset0 {name};}}\n')
        lines.append('}\n')
        return ''.join(lines)


# ---------------------------------------------------------------------------
# Color table builder
# ---------------------------------------------------------------------------

class ColorTable:
    """Collect all unique RGB colors and build an RTF color table.
    
    Index 0 is always the "auto" entry (empty); color indices in RTF are 1-based.
    """

    def __init__(self):
        self._colors: list[tuple[int, int, int] | None] = [None]  # slot 0 = auto
        self._index: dict[tuple, int] = {}

    def register(self, rgb: tuple[int, int, int]) -> int:
        if rgb not in self._index:
            self._index[rgb] = len(self._colors)
            self._colors.append(rgb)
        return self._index[rgb]

    def to_rtf(self) -> str:
        lines = ['{\\colortbl\n']
        for entry in self._colors:
            if entry is None:
                lines.append(';\n')  # auto color
            else:
                r, g, b = entry
                lines.append(f'\\red{r}\\green{g}\\blue{b};\n')
        lines.append('}\n')
        return ''.join(lines)


# ---------------------------------------------------------------------------
# Section / page properties
# ---------------------------------------------------------------------------

def _read_section_properties(doc: Document) -> str:
    """Extract page size and margin settings from the last section."""
    try:
        section = doc.sections[-1]
        # All measurements in EMUs; 914400 EMU = 1 inch; RTF twips: 1 inch = 1440 twips
        def to_twips(emu):
            return int(emu / 914400 * 1440)

        pw = to_twips(section.page_width)
        ph = to_twips(section.page_height)
        ml = to_twips(section.left_margin)
        mr = to_twips(section.right_margin)
        mt = to_twips(section.top_margin)
        mb = to_twips(section.bottom_margin)

        orientation = ''
        if section.orientation and section.orientation != 0:
            orientation = '\\landscape'

        return (
            f'\\paperw{pw}\\paperh{ph}{orientation}\n'
            f'\\margl{ml}\\margr{mr}\\margt{mt}\\margb{mb}\n'
        )
    except Exception:
        # Fall back to sensible defaults (letter, 1-inch margins)
        return '\\paperw12240\\paperh15840\n\\margl1440\\margr1440\\margt1440\\margb1440\n'


# ---------------------------------------------------------------------------
# Run-level formatting
# ---------------------------------------------------------------------------

def _run_to_rtf(run, font_table: FontTable, color_table: ColorTable,
                default_font: str = "Calibri", default_size: int = 24) -> str:
    """Convert a single docx run to RTF, preserving all character formatting."""
    text = run.text
    if not text:
        return ''

    font = run.font
    escaped = _escape_rtf(text)

    # Font family
    font_name = font.name or default_font
    f_idx = font_table.get_index(font_name)

    # Font size (half-points)
    fs = _half_points(font.size) if font.size else default_size

    # Colour
    color_tag = ''
    try:
        if font.color and font.color.type is not None and font.color.rgb:
            rgb = font.color.rgb  # RGBColor
            idx = color_table.register((rgb[0], rgb[1], rgb[2]))
            color_tag = f'\\cf{idx}'
    except Exception:
        pass

    # Toggles
    bold      = '\\b'      if font.bold      else ''
    italic    = '\\i'      if font.italic     else ''
    underline = '\\ul'     if font.underline  else ''
    strike    = '\\strike' if font.strike     else ''

    open_tags  = f'\\f{f_idx}\\fs{fs}{color_tag}{bold}{italic}{underline}{strike} '
    close_tags = (
        ('\\b0'      if font.bold      else '') +
        ('\\i0'      if font.italic    else '') +
        ('\\ulnone'  if font.underline else '') +
        ('\\strike0' if font.strike    else '')
    )

    return f'{{{open_tags}{escaped}{close_tags}}}'


# ---------------------------------------------------------------------------
# Paragraph-level formatting
# ---------------------------------------------------------------------------

def _para_prefix(para, default_size: int = 24) -> str:
    """Build the RTF paragraph formatting prefix (pard + spacing + alignment)."""
    pf = para.paragraph_format

    # Spacing
    def twips_from_pt(length_obj):
        if length_obj is None:
            return None
        try:
            return int(length_obj.pt * 20)  # 1pt = 20 twips
        except Exception:
            return None

    sb = twips_from_pt(pf.space_before) or 0
    sa = twips_from_pt(pf.space_after) or 0
    li = twips_from_pt(pf.left_indent) or 0
    fi = twips_from_pt(pf.first_line_indent) or 0

    # Alignment
    align_map = {
        'CENTER':  '\\qc',
        'RIGHT':   '\\qr',
        'JUSTIFY': '\\qj',
        'LEFT':    '\\ql',
    }
    try:
        raw = str(para.alignment)
        # Handles both 'WD_ALIGN_PARAGRAPH.CENTER' and 'CENTER (1)' formats
        key = raw.split('.')[-1].split('(')[0].strip().upper()
        align = align_map.get(key, '\\ql')
    except Exception:
        align = '\\ql'

    parts = [f'\\pard']
    # Don't apply left/first-line indent to centered or right-aligned paragraphs —
    # negative indent values (e.g. on Title) would misplace the text.
    if align not in ('\\qc', '\\qr'):
        if li > 0:
            parts.append(f'\\li{li}')
        if fi:
            parts.append(f'\\fi{fi}')
    if sb:
        parts.append(f'\\sb{sb}')
    if sa:
        parts.append(f'\\sa{sa}')
    parts.append(align)
    return ''.join(parts)


# ---------------------------------------------------------------------------
# Relationship map (rId -> media path inside zip)
# ---------------------------------------------------------------------------

def _build_rel_map(docx_file) -> dict:
    """Return {rId: zip_internal_path} for all image relationships."""
    import zipfile, xml.etree.ElementTree as ET

    ns_rel = 'http://schemas.openxmlformats.org/package/2006/relationships'
    IMG_TYPE = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/image'
    rel_map = {}

    try:
        if isinstance(docx_file, io.BytesIO):
            pos = docx_file.tell(); docx_file.seek(0)
        with zipfile.ZipFile(docx_file if isinstance(docx_file, str) else docx_file) as z:
            rels_path = 'word/_rels/document.xml.rels'
            if rels_path in z.namelist():
                with z.open(rels_path) as f:
                    root = ET.parse(f).getroot()
                for rel in root.findall(f'{{{ns_rel}}}Relationship'):
                    if rel.get('Type') == IMG_TYPE:
                        rid    = rel.get('Id')
                        target = rel.get('Target')  # e.g. "media/image1.png"
                        rel_map[rid] = f'word/{target}'
        if isinstance(docx_file, io.BytesIO):
            docx_file.seek(pos)
    except Exception:
        pass

    return rel_map


# ---------------------------------------------------------------------------
# Image renderer: extract image bytes from zip, emit RTF \pict block
# ---------------------------------------------------------------------------

def _render_anchored_image_rtf(docx_file, zip_path: str,
                                cx_emu: int, cy_emu: int,
                                pos_x_emu: int, pos_y_emu: int) -> str:
    """
    Render a floating/anchored image as an RTF absolutely-positioned \\shp block.
    pos_x/pos_y are in EMU from the page origin.
    cx/cy are the image dimensions in EMU.
    """
    import zipfile, struct

    EMU_PER_INCH  = 914400
    TWIP_PER_INCH = 1440

    def emu_to_twips(v): return int(v / EMU_PER_INCH * TWIP_PER_INCH)

    left   = emu_to_twips(pos_x_emu)
    top    = emu_to_twips(pos_y_emu)
    right  = left + emu_to_twips(cx_emu)
    bottom = top  + emu_to_twips(cy_emu)

    try:
        if isinstance(docx_file, io.BytesIO):
            pos = docx_file.tell(); docx_file.seek(0)
        with zipfile.ZipFile(docx_file if isinstance(docx_file, str) else docx_file) as z:
            if zip_path not in z.namelist():
                return ''
            img_bytes = z.read(zip_path)
        if isinstance(docx_file, io.BytesIO):
            docx_file.seek(pos)
    except Exception:
        return ''

    ext = zip_path.rsplit('.', 1)[-1].lower()
    if ext == 'png':
        pict_type = '\\pngblip'
    elif ext in ('jpg', 'jpeg'):
        pict_type = '\\jpegblip'
    else:
        return ''

    hex_data = img_bytes.hex()
    goal_w = emu_to_twips(cx_emu)
    goal_h = emu_to_twips(cy_emu)

    # RTF \shp with absolute page positioning
    # shpbxpage / shpbypage = position relative to page (not margin)
    # shpwr=0 = no text wrap (like wrapNone)
    return (
        '{\\shp{\\*\\shpinst'
        f'\\shpleft{left}\\shptop{top}\\shpright{right}\\shpbottom{bottom}'
        '\\shpfhdr0\\shpbxpage\\shpbypage\\shpwr0\\shpfblwtxt0'
        '{\\sp{\\sn shapeType}{\\sv 75}}'          # 75 = picture frame
        '{\\sp{\\sn fFlipH}{\\sv 0}}'
        '{\\sp{\\sn fFlipV}{\\sv 0}}'
        '{\\sp{\\sn pib}'
        '{\\sv {'
        f'\\pict{pict_type}'
        f'\\picwgoal{goal_w}\\pichgoal{goal_h}\n'
        f'{hex_data}'
        '}}}'
        '}}\n'
    )


# ---------------------------------------------------------------------------
# Numbering / bullet resolver
# ---------------------------------------------------------------------------

def _build_numbering_map(docx_file) -> dict:
    """
    Parse word/numbering.xml and return a dict:
      numId (str) -> { ilvl (str) -> { 'fmt': str, 'char': str, 'left': int, 'hanging': int } }

    'char' is the literal bullet character (e.g. '●', '•', '-').
    For decimal/lowerLetter etc. we fall back to a plain hyphen since
    true auto-numbering requires state; this covers the common bullet case.
    """
    import zipfile, xml.etree.ElementTree as ET

    ns = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
    result: dict = {}

    try:
        if isinstance(docx_file, str):
            zpath = docx_file
        else:
            # BytesIO — reset and read
            pos = docx_file.tell()
            docx_file.seek(0)
            zpath = docx_file
        with zipfile.ZipFile(zpath) as z:
            if 'word/numbering.xml' not in z.namelist():
                return result
            with z.open('word/numbering.xml') as f:
                root = ET.parse(f).getroot()

        # abstractNum id -> levels
        abstract: dict = {}
        for absNum in root.findall(f'{{{ns}}}abstractNum'):
            absId = absNum.get(f'{{{ns}}}abstractNumId')
            levels = {}
            for lvl in absNum.findall(f'{{{ns}}}lvl'):
                ilvl = lvl.get(f'{{{ns}}}ilvl')
                numFmt_el = lvl.find(f'{{{ns}}}numFmt')
                lvlText_el = lvl.find(f'{{{ns}}}lvlText')
                pPr = lvl.find(f'{{{ns}}}pPr')
                ind = pPr.find(f'{{{ns}}}ind') if pPr is not None else None

                fmt  = numFmt_el.get(f'{{{ns}}}val') if numFmt_el is not None else 'bullet'
                text = lvlText_el.get(f'{{{ns}}}val') if lvlText_el is not None else '\u2022'
                left    = int(ind.get(f'{{{ns}}}left',    '720')) if ind is not None else 720
                hanging = int(ind.get(f'{{{ns}}}hanging', '360')) if ind is not None else 360

                # For non-bullet formats, use a simple dash
                if fmt != 'bullet':
                    text = '-'

                levels[ilvl] = {'fmt': fmt, 'char': text, 'left': left, 'hanging': hanging}
            abstract[absId] = levels

        # numId -> abstractNumId mapping
        for num in root.findall(f'{{{ns}}}num'):
            numId = num.get(f'{{{ns}}}numId')
            absRef = num.find(f'{{{ns}}}abstractNumId')
            absId  = absRef.get(f'{{{ns}}}val') if absRef is not None else None
            result[numId] = abstract.get(absId, {})

        if isinstance(docx_file, io.BytesIO):
            docx_file.seek(pos)

    except Exception:
        pass

    return result


def _get_list_info(para, numbering_map: dict) -> dict | None:
    """Return bullet info dict for a list paragraph, or None if not a list."""
    ns = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
    numPr = para._element.find(f'.//{{{ns}}}numPr')
    if numPr is None:
        return None
    ilvl_el = numPr.find(f'{{{ns}}}ilvl')
    numId_el = numPr.find(f'{{{ns}}}numId')
    if ilvl_el is None or numId_el is None:
        return None
    ilvl  = ilvl_el.get(f'{{{ns}}}val', '0')
    numId = numId_el.get(f'{{{ns}}}val', '0')
    if numId == '0':
        return None
    return numbering_map.get(numId, {}).get(ilvl, {
        'char': '\u2022', 'left': 720, 'hanging': 360
    })


def _collect_default_font_and_size(doc: Document, font_table: FontTable) -> tuple[str, int]:
    """Try to read the document-level default font and size from styles."""
    default_font = "Calibri"
    default_size = 24  # 12pt

    try:
        normal = doc.styles['Normal']
        if normal.font.name:
            default_font = normal.font.name
        if normal.font.size:
            default_size = _half_points(normal.font.size)
    except Exception:
        pass

    font_table.register(default_font)
    return default_font, default_size


def _collect_all_fonts(doc: Document, font_table: FontTable):
    """Pre-scan the document to register every font into the font table."""
    for para in doc.paragraphs:
        for run in para.runs:
            if run.font.name:
                font_table.register(run.font.name)
    # Also scan tables
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for para in cell.paragraphs:
                    for run in para.runs:
                        if run.font.name:
                            font_table.register(run.font.name)


# ---------------------------------------------------------------------------
# Public API: docx → RTF
# ---------------------------------------------------------------------------

def convert_docx_to_rtf(docx_file: Union[str, io.BytesIO]) -> bytes:
    """
    Convert a Word document to RTF, faithfully preserving:
      - Font family (per run)
      - Font size (per run)
      - Bold, italic, underline, strikethrough (per run)
      - Font colour (per run)
      - Paragraph spacing, indentation, alignment
      - Page size and margins
      - Bullet characters read directly from numbering.xml (exact glyph, indent)
      - Title style: centered, actual run sizes/colors, not overridden
      - Tables (basic)
    """
    doc = Document(docx_file)

    font_table  = FontTable()
    color_table = ColorTable()

    # Build bullet/numbering lookup from the docx zip
    numbering_map = _build_numbering_map(docx_file)

    # Build relationship map for images
    rel_map = _build_rel_map(docx_file)

    # Namespace shortcuts for image detection
    _NS_A   = 'http://schemas.openxmlformats.org/drawingml/2006/main'
    _NS_R   = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
    _NS_WP  = 'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing'

    # Pre-scan: register all fonts so the font table is complete
    _collect_all_fonts(doc, font_table)
    default_font, default_size = _collect_default_font_and_size(doc, font_table)

    # We build body content first, then prepend the header (which needs the
    # complete font/color tables).
    body_parts: list[str] = []

    def render_paragraph(para) -> str:
        parts = []

        # --- Anchored image detection ---
        _NS_WPA = 'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing'
        anchor = para._element.find(f'.//{{{_NS_WPA}}}anchor')
        if anchor is not None:
            blip = para._element.find(f'.//{{{_NS_A}}}blip')
            if blip is not None:
                rId = blip.get(f'{{{_NS_R}}}embed')
                zip_path = rel_map.get(rId, '')
                if zip_path:
                    extent = anchor.find(f'{{{_NS_WPA}}}extent')
                    cx = int(extent.get('cx', '4572000')) if extent is not None else 4572000
                    cy = int(extent.get('cy', '3429000')) if extent is not None else 3429000

                    # Absolute position from page origin
                    posH_el = anchor.find(f'{{{_NS_WPA}}}positionH')
                    posV_el = anchor.find(f'{{{_NS_WPA}}}positionV')
                    posH_off = posH_el.find(f'{{{_NS_WPA}}}posOffset') if posH_el is not None else None
                    posV_off = posV_el.find(f'{{{_NS_WPA}}}posOffset') if posV_el is not None else None
                    pos_x = int(posH_off.text) if posH_off is not None and posH_off.text else 0
                    pos_y = int(posV_off.text) if posV_off is not None and posV_off.text else 0

                    img_rtf = _render_anchored_image_rtf(docx_file, zip_path, cx, cy, pos_x, pos_y)
                    if img_rtf:
                        parts.append(img_rtf)

        # --- Page break detection (w:br w:type="page") in any run ---
        _NS_W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
        has_page_break = any(
            br.get(f'{{{_NS_W}}}type') == 'page'
            for br in para._element.findall(f'.//{{{_NS_W}}}br')
        )

        # Render text content of this paragraph (may be empty if image-only)
        text = para.text.strip()
        style_name = (para.style.name or '').lower()

        # Check if this is a list paragraph FIRST — takes priority over heading detection
        list_info = _get_list_info(para, numbering_map)
        if list_info:
            bullet_char = list_info.get('char', '\u2022')
            left    = list_info.get('left', 720)
            hanging = list_info.get('hanging', 360)
            bullet_rtf = _escape_rtf(bullet_char)
            runs_str = ''.join(
                _run_to_rtf(run, font_table, color_table, default_font, default_size)
                for run in para.runs
            )
            if not runs_str and text:
                f_idx = font_table.get_index(default_font)
                runs_str = f'{{\\f{f_idx}\\fs{default_size} {_escape_rtf(text)}}}'
            parts.append(
                f'\\pard\\li{left}\\fi-{hanging}\\sa80\\ql '
                f'{bullet_rtf}\\tab {runs_str}\\par\n'
            )
        else:
            # Headings — but NOT Title
            heading_fs = None
            is_title = para.style.name == 'Title'
            if not is_title:
                if 'heading 1' in style_name:
                    heading_fs = 40
                elif 'heading 2' in style_name:
                    heading_fs = 36
                elif 'heading 3' in style_name:
                    heading_fs = 32
                elif 'heading 4' in style_name:
                    heading_fs = 28

            prefix = _para_prefix(para, default_size)
            runs_rtf = []
            for run in para.runs:
                r = _run_to_rtf(run, font_table, color_table, default_font, default_size)
                if heading_fs and r:
                    orig_fs = _half_points(run.font.size) if run.font.size else default_size
                    r = r.replace(f'\\fs{orig_fs}', f'\\fs{heading_fs}')
                runs_rtf.append(r)

            runs_str = ''.join(runs_rtf)
            if not runs_str and text:
                escaped = _escape_rtf(text)
                fs = heading_fs or default_size
                bold = '\\b ' if heading_fs else ''
                bold_close = '\\b0' if heading_fs else ''
                font_idx = font_table.get_index(default_font)
                runs_str = f'\\f{font_idx}\\fs{fs} {bold}{escaped}{bold_close}'

            if runs_str:
                parts.append(f'{prefix} {runs_str}\\par\n')
            elif not parts:  # truly empty paragraph, no image either
                parts.append(f'{prefix}\\par\n')
            # If we already added an image and there's no text, skip empty par

        # Page break goes AFTER the paragraph content
        if has_page_break:
            parts.append('\\page\n')

        return ''.join(parts)

    def render_table(table) -> str:
        parts = []
        col_count = max(len(row.cells) for row in table.rows)
        col_width = int(9360 / max(col_count, 1))  # twips, approx A4 width

        for row in table.rows:
            # Write cell definitions
            cell_defs = ''
            x = 0
            for _ in row.cells:
                x += col_width
                cell_defs += f'\\cellx{x}'

            parts.append(f'\\trowd\\trgaph108\\trleft0{cell_defs}\n')
            for cell in row.cells:
                parts.append('\\pard\\intbl ')
                for para in cell.paragraphs:
                    for run in para.runs:
                        parts.append(_run_to_rtf(run, font_table, color_table,
                                                  default_font, default_size))
                parts.append('\\cell\n')
            parts.append('\\row\n')
        return ''.join(parts)

    # Iterate document body in order (paragraphs and tables)
    for block in doc.element.body:
        tag = block.tag.split('}')[-1]  # strip namespace
        if tag == 'p':
            # Find the matching paragraph object
            para = None
            for p in doc.paragraphs:
                if p._element is block:
                    para = p
                    break
            if para is not None:
                body_parts.append(render_paragraph(para))
            else:
                body_parts.append('\\par\n')
        elif tag == 'tbl':
            # Find matching table
            for t in doc.tables:
                if t._element is block:
                    body_parts.append(render_table(t))
                    break
        else:
            body_parts.append('\\par\n')

    # --- Assemble final RTF ---
    page_props = _read_section_properties(doc)

    header = (
        '{\\rtf1\\ansi\\ansicpg1252\\deff0\n'
        + font_table.to_rtf()
        + color_table.to_rtf()
        + '\\widowctrl\\hyphauto\n'
        + page_props
    )

    return (header + ''.join(body_parts) + '}\n').encode('ascii', errors='replace')


# ---------------------------------------------------------------------------
# Public API: markdown → RTF
# ---------------------------------------------------------------------------

def _inline_markdown_to_rtf(text: str, font_table: FontTable, color_table: ColorTable,
                              default_font: str, default_fs: int) -> str:
    """Convert inline markdown (bold, italic, code) within a line to RTF runs."""
    f_idx = font_table.get_index(default_font)
    result = []
    # Parse inline patterns left-to-right
    pattern = re.compile(r'(\*\*\*(.+?)\*\*\*|\*\*(.+?)\*\*|\*(.+?)\*|`(.+?)`)')
    last = 0
    for m in pattern.finditer(text):
        # Plain text before match
        plain = text[last:m.start()]
        if plain:
            result.append(f'{{\\f{f_idx}\\fs{default_fs} {_escape_rtf(plain)}}}')
        if m.group(2):  # bold+italic ***
            result.append(f'{{\\f{f_idx}\\fs{default_fs}\\b\\i {_escape_rtf(m.group(2))}\\b0\\i0}}')
        elif m.group(3):  # bold **
            result.append(f'{{\\f{f_idx}\\fs{default_fs}\\b {_escape_rtf(m.group(3))}\\b0}}')
        elif m.group(4):  # italic *
            result.append(f'{{\\f{f_idx}\\fs{default_fs}\\i {_escape_rtf(m.group(4))}\\i0}}')
        elif m.group(5):  # inline code `
            mono_idx = font_table.register("Courier New")
            result.append(f'{{\\f{mono_idx}\\fs{default_fs} {_escape_rtf(m.group(5))}}}')
        last = m.end()
    # Remaining text
    tail = text[last:]
    if tail:
        result.append(f'{{\\f{f_idx}\\fs{default_fs} {_escape_rtf(tail)}}}')
    return ''.join(result)


def convert_markdown_to_rtf(markdown_text: str) -> bytes:
    """Convert markdown text to RTF with inline formatting support."""
    font_table  = FontTable()
    color_table = ColorTable()
    default_font = "Calibri"
    default_fs   = 24  # 12pt
    font_table.register(default_font)

    body_parts: list[str] = []
    lines = markdown_text.split('\n')

    for line in lines:
        line = line.rstrip()

        if not line:
            body_parts.append('\\par\n')
            continue

        # Headings
        if line.startswith('#### '):
            text = line[5:].strip()
            f_idx = font_table.get_index(default_font)
            body_parts.append(f'\\pard\\sb180\\sa90\\ql\\f{f_idx}\\fs28\\b {_escape_rtf(text)}\\b0\\par\n')
        elif line.startswith('### '):
            text = line[4:].strip()
            f_idx = font_table.get_index(default_font)
            body_parts.append(f'\\pard\\sb200\\sa100\\ql\\f{f_idx}\\fs32\\b {_escape_rtf(text)}\\b0\\par\n')
        elif line.startswith('## '):
            text = line[3:].strip()
            f_idx = font_table.get_index(default_font)
            body_parts.append(f'\\pard\\sb250\\sa120\\ql\\f{f_idx}\\fs36\\b {_escape_rtf(text)}\\b0\\par\n')
        elif line.startswith('# '):
            text = line[2:].strip()
            f_idx = font_table.get_index(default_font)
            body_parts.append(f'\\pard\\sb300\\sa150\\ql\\f{f_idx}\\fs40\\b {_escape_rtf(text)}\\b0\\par\n')
        elif line.startswith('- ') or line.startswith('* ') or line.startswith('+ '):
            text = line[2:].strip()
            inline = _inline_markdown_to_rtf(text, font_table, color_table, default_font, default_fs)
            body_parts.append(f'\\pard\\li720\\fi-360\\sa80\\ql \\u8226? {inline}\\par\n')
        elif re.match(r'^\d+\.\s+', line):
            text = re.sub(r'^\d+\.\s+', '', line)
            inline = _inline_markdown_to_rtf(text, font_table, color_table, default_font, default_fs)
            body_parts.append(f'\\pard\\li720\\fi-360\\sa80\\ql {inline}\\par\n')
        elif line.startswith('```'):
            # Code fence — just render as monospaced (simplified)
            mono_idx = font_table.register("Courier New")
            body_parts.append(f'\\pard\\sa80\\ql\\f{mono_idx}\\fs20 {_escape_rtf(line)}\\par\n')
        elif line.startswith('> '):
            # Blockquote
            text = line[2:].strip()
            inline = _inline_markdown_to_rtf(text, font_table, color_table, default_font, default_fs)
            body_parts.append(f'\\pard\\li720\\sa100\\ql\\cf1\\i {inline}\\i0\\cf0\\par\n')
        else:
            inline = _inline_markdown_to_rtf(line, font_table, color_table, default_font, default_fs)
            body_parts.append(f'\\pard\\sa100\\ql {inline}\\par\n')

    header = (
        '{\\rtf1\\ansi\\ansicpg1252\\deff0\n'
        + font_table.to_rtf()
        + color_table.to_rtf()
        + '\\widowctrl\\hyphauto\n'
        + '\\paperw12240\\paperh15840\n'
        + '\\margl1440\\margr1440\\margt1440\\margb1440\n'
    )
    return (header + ''.join(body_parts) + '}\n').encode('ascii', errors='replace')


# ---------------------------------------------------------------------------
# Public API: plain text → RTF
# ---------------------------------------------------------------------------

def convert_text_to_rtf(text_content: str) -> bytes:
    """Convert plain text to RTF."""
    font_table  = FontTable()
    color_table = ColorTable()
    default_font = "Calibri"
    default_fs   = 24
    f_idx = font_table.register(default_font)

    body_parts = []
    for line in text_content.split('\n'):
        if not line.strip():
            body_parts.append('\\par\n')
        else:
            body_parts.append(f'\\pard\\sa100\\ql\\f{f_idx}\\fs{default_fs} {_escape_rtf(line)}\\par\n')

    header = (
        '{\\rtf1\\ansi\\ansicpg1252\\deff0\n'
        + font_table.to_rtf()
        + color_table.to_rtf()
        + '\\widowctrl\\hyphauto\n'
        + '\\paperw12240\\paperh15840\n'
        + '\\margl1440\\margr1440\\margt1440\\margb1440\n'
    )
    return (header + ''.join(body_parts) + '}\n').encode('ascii', errors='replace')
