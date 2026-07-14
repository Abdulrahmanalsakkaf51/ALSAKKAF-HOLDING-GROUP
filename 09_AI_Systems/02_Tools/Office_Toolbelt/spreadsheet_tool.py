"""AOS Office Toolbelt - spreadsheet tool (PRJ-013). Standard library only.

Creates and edits REAL .xlsx workbooks by writing the Office Open XML parts
directly (an .xlsx file is a ZIP of XML). No openpyxl, no external packages.

Supported:
  * Multiple sheets, header styling (bold white on navy), zebra striping
  * Text, integer, and float cells; ISO date strings stored as text
  * Column widths, freeze header row, basic number handling
  * Reading values back from workbooks (inline strings, shared strings, numbers)
  * Appending rows to workbooks created by this tool or similarly simple files

Not supported (honest scope): charts, formulas evaluation, pivot tables,
editing complex third-party workbooks with formatting preservation.
"""

import os
import re
import shutil
import zipfile
from xml.sax.saxutils import escape

BRAND_NAVY = "FF0A2342"
BRAND_HEADER_TEXT = "FFFFFFFF"
ZEBRA_FILL = "FFEFF4FB"


def _col_letter(idx):
    """1 -> A, 27 -> AA."""
    letters = ""
    while idx > 0:
        idx, rem = divmod(idx - 1, 26)
        letters = chr(65 + rem) + letters
    return letters


CONTENT_TYPES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>
{sheet_overrides}
</Types>"""

ROOT_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>"""

STYLES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
<fonts count="2">
<font><sz val="11"/><name val="Calibri"/></font>
<font><b/><color rgb="{header_text}"/><sz val="11"/><name val="Calibri"/></font>
</fonts>
<fills count="4">
<fill><patternFill patternType="none"/></fill>
<fill><patternFill patternType="gray125"/></fill>
<fill><patternFill patternType="solid"><fgColor rgb="{navy}"/><bgColor indexed="64"/></patternFill></fill>
<fill><patternFill patternType="solid"><fgColor rgb="{zebra}"/><bgColor indexed="64"/></patternFill></fill>
</fills>
<borders count="2">
<border><left/><right/><top/><bottom/><diagonal/></border>
<border><left style="thin"><color auto="1"/></left><right style="thin"><color auto="1"/></right><top style="thin"><color auto="1"/></top><bottom style="thin"><color auto="1"/></bottom><diagonal/></border>
</borders>
<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>
<cellXfs count="4">
<xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>
<xf numFmtId="0" fontId="1" fillId="2" borderId="1" xfId="0" applyFont="1" applyFill="1" applyBorder="1"/>
<xf numFmtId="0" fontId="0" fillId="0" borderId="1" xfId="0" applyBorder="1"/>
<xf numFmtId="0" fontId="0" fillId="3" borderId="1" xfId="0" applyFill="1" applyBorder="1"/>
</cellXfs>
</styleSheet>""".format(header_text=BRAND_HEADER_TEXT, navy=BRAND_NAVY, zebra=ZEBRA_FILL)


def _cell_xml(ref, value, style_id):
    if isinstance(value, bool):
        value = "yes" if value else "no"
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return '<c r="%s" s="%d" t="n"><v>%s</v></c>' % (ref, style_id, value)
    text = escape(str(value if value is not None else ""))
    return ('<c r="%s" s="%d" t="inlineStr"><is><t xml:space="preserve">%s</t></is></c>'
            % (ref, style_id, text))


def _sheet_xml(headers, rows, freeze_header=True, zebra=True, col_widths=None):
    parts = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
             '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">']
    if freeze_header and headers:
        parts.append('<sheetViews><sheetView workbookViewId="0">'
                     '<pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/>'
                     '</sheetView></sheetViews>')
    if col_widths is None and headers:
        col_widths = []
        for i, h in enumerate(headers):
            longest = len(str(h))
            for row in rows:
                if i < len(row):
                    longest = max(longest, len(str(row[i])))
            col_widths.append(min(max(longest + 3, 10), 45))
    if col_widths:
        parts.append("<cols>")
        for i, w in enumerate(col_widths, start=1):
            parts.append('<col min="%d" max="%d" width="%s" customWidth="1"/>' % (i, i, w))
        parts.append("</cols>")
    parts.append("<sheetData>")
    rnum = 0
    if headers:
        rnum += 1
        cells = "".join(_cell_xml("%s%d" % (_col_letter(c + 1), rnum), h, 1)
                        for c, h in enumerate(headers))
        parts.append('<row r="%d">%s</row>' % (rnum, cells))
    for row in rows:
        rnum += 1
        style = 3 if (zebra and rnum % 2 == 1) else 2
        cells = "".join(_cell_xml("%s%d" % (_col_letter(c + 1), rnum), v, style)
                        for c, v in enumerate(row))
        parts.append('<row r="%d">%s</row>' % (rnum, cells))
    parts.append("</sheetData></worksheet>")
    return "".join(parts)


def create_workbook(path, sheets):
    """sheets: list of dicts {"name", "headers", "rows", optional "col_widths"}."""
    if not sheets:
        raise ValueError("At least one sheet required")
    sheet_overrides = []
    workbook_sheets = []
    workbook_rels = []
    sheet_parts = {}
    for i, sheet in enumerate(sheets, start=1):
        part = "xl/worksheets/sheet%d.xml" % i
        sheet_overrides.append(
            '<Override PartName="/%s" ContentType="application/vnd.openxmlformats-'
            'officedocument.spreadsheetml.worksheet+xml"/>' % part)
        name = escape(sheet["name"][:31])
        workbook_sheets.append('<sheet name="%s" sheetId="%d" r:id="rId%d"/>' % (name, i, i))
        workbook_rels.append(
            '<Relationship Id="rId%d" Type="http://schemas.openxmlformats.org/'
            'officeDocument/2006/relationships/worksheet" Target="worksheets/sheet%d.xml"/>'
            % (i, i))
        sheet_parts[part] = _sheet_xml(sheet.get("headers"), sheet.get("rows", []),
                                       col_widths=sheet.get("col_widths"))
    styles_rid = len(sheets) + 1
    workbook_rels.append(
        '<Relationship Id="rId%d" Type="http://schemas.openxmlformats.org/'
        'officeDocument/2006/relationships/styles" Target="styles.xml"/>' % styles_rid)

    workbook_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"'
        ' xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        "<sheets>%s</sheets></workbook>" % "".join(workbook_sheets))
    workbook_rels_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        "%s</Relationships>" % "".join(workbook_rels))

    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml",
                   CONTENT_TYPES.format(sheet_overrides="".join(sheet_overrides)))
        z.writestr("_rels/.rels", ROOT_RELS)
        z.writestr("xl/workbook.xml", workbook_xml)
        z.writestr("xl/_rels/workbook.xml.rels", workbook_rels_xml)
        z.writestr("xl/styles.xml", STYLES)
        for part, xml in sheet_parts.items():
            z.writestr(part, xml)
    return path


_CELL_RE = re.compile(r"<c ([^>]*?)(?:/>|>(.*?)</c>)", re.S)
_REF_RE = re.compile(r'r="([A-Z]+)(\d+)"')
_TYPE_RE = re.compile(r't="(\w+)"')
_V_RE = re.compile(r"<v>(.*?)</v>", re.S)
_T_RE = re.compile(r"<t[^>]*>(.*?)</t>", re.S)


def _unescape(text):
    return (text.replace("&lt;", "<").replace("&gt;", ">")
            .replace("&quot;", '"').replace("&apos;", "'").replace("&amp;", "&"))


def read_workbook(path, sheet_index=1):
    """Return rows (list of lists) from sheet N. Handles inline strings,
    shared strings, and numbers."""
    with zipfile.ZipFile(path) as z:
        shared = []
        if "xl/sharedStrings.xml" in z.namelist():
            sxml = z.read("xl/sharedStrings.xml").decode("utf-8")
            shared = [_unescape(m) for m in
                      re.findall(r"<si>.*?<t[^>]*>(.*?)</t>.*?</si>", sxml, re.S)]
        sheet_name = "xl/worksheets/sheet%d.xml" % sheet_index
        xml = z.read(sheet_name).decode("utf-8")
    rows = {}
    for attrs, body in _CELL_RE.findall(xml):
        ref = _REF_RE.search(attrs)
        if not ref:
            continue
        col, rownum = ref.group(1), int(ref.group(2))
        tmatch = _TYPE_RE.search(attrs)
        ctype = tmatch.group(1) if tmatch else ""
        body = body or ""
        if ctype == "inlineStr":
            m = _T_RE.search(body)
            value = _unescape(m.group(1)) if m else ""
        elif ctype == "s":
            m = _V_RE.search(body)
            value = shared[int(m.group(1))] if m else ""
        else:
            m = _V_RE.search(body)
            raw = m.group(1) if m else ""
            try:
                value = int(raw)
            except ValueError:
                try:
                    value = float(raw)
                except ValueError:
                    value = _unescape(raw)
        col_idx = 0
        for ch in col:
            col_idx = col_idx * 26 + (ord(ch) - 64)
        rows.setdefault(rownum, {})[col_idx] = value
    out = []
    for rownum in sorted(rows):
        row = rows[rownum]
        width = max(row)
        out.append([row.get(c, "") for c in range(1, width + 1)])
    return out


def append_rows(path, new_rows, sheet_index=1):
    """Append rows to an existing workbook by rewriting the sheet XML.
    Designed for workbooks created by this tool and similar simple files."""
    existing = read_workbook(path, sheet_index)
    headers = existing[0] if existing else None
    body = existing[1:] if existing else []
    body.extend(new_rows)
    tmp = path + ".tmp"
    sheet_part = "xl/worksheets/sheet%d.xml" % sheet_index
    new_sheet_xml = _sheet_xml(headers, body)
    with zipfile.ZipFile(path) as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.namelist():
            if item == sheet_part:
                zout.writestr(item, new_sheet_xml)
            else:
                zout.writestr(item, zin.read(item))
    shutil.move(tmp, path)
    return path
