"""AOS Office Toolbelt - document tool (PRJ-013). Standard library only.

Creates REAL .docx documents by writing Office Open XML parts directly
(a .docx file is a ZIP of XML). No python-docx, no external packages.

Supported blocks:
  {"type": "title",     "text": "..."}
  {"type": "heading",   "text": "...", "level": 1|2}
  {"type": "paragraph", "text": "...", "bold": False}
  {"type": "bullets",   "items": ["...", "..."]}
  {"type": "table",     "headers": [...], "rows": [[...], ...]}
  {"type": "note",      "text": "..."}   (small gray review note)

Also supported: replacing {{placeholders}} in documents created by this tool.

Not supported (honest scope): images, comments threads, tracked changes,
editing complex third-party documents with formatting preservation.
"""

import os
import re
import shutil
import zipfile
from xml.sax.saxutils import escape

CONTENT_TYPES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
</Types>"""

ROOT_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""

DOC_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>"""

STYLES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
<w:docDefaults><w:rPrDefault><w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/><w:sz w:val="22"/></w:rPr></w:rPrDefault></w:docDefaults>
<w:style w:type="paragraph" w:styleId="Normal" w:default="1"><w:name w:val="Normal"/></w:style>
<w:style w:type="paragraph" w:styleId="Title"><w:name w:val="Title"/><w:basedOn w:val="Normal"/>
<w:pPr><w:spacing w:after="240"/></w:pPr>
<w:rPr><w:b/><w:sz w:val="44"/><w:color w:val="0A2342"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="heading 1"/><w:basedOn w:val="Normal"/>
<w:pPr><w:spacing w:before="240" w:after="120"/><w:outlineLvl w:val="0"/></w:pPr>
<w:rPr><w:b/><w:sz w:val="32"/><w:color w:val="0A2342"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Heading2"><w:name w:val="heading 2"/><w:basedOn w:val="Normal"/>
<w:pPr><w:spacing w:before="200" w:after="100"/><w:outlineLvl w:val="1"/></w:pPr>
<w:rPr><w:b/><w:sz w:val="26"/><w:color w:val="1E6FFF"/></w:rPr></w:style>
</w:styles>"""


def _run(text, bold=False, color=None, size=None):
    props = []
    if bold:
        props.append("<w:b/>")
    if color:
        props.append('<w:color w:val="%s"/>' % color)
    if size:
        props.append('<w:sz w:val="%d"/>' % size)
    rpr = "<w:rPr>%s</w:rPr>" % "".join(props) if props else ""
    return ('<w:r>%s<w:t xml:space="preserve">%s</w:t></w:r>'
            % (rpr, escape(str(text))))


def _paragraph(text, style=None, bold=False, color=None, size=None):
    ppr = '<w:pPr><w:pStyle w:val="%s"/></w:pPr>' % style if style else ""
    return "<w:p>%s%s</w:p>" % (ppr, _run(text, bold=bold, color=color, size=size))


def _bullet(text):
    ppr = ('<w:pPr><w:ind w:left="360" w:hanging="200"/></w:pPr>')
    return "<w:p>%s%s%s</w:p>" % (ppr, _run("• ", bold=True, color="1E6FFF"),
                                  _run(text))


def _table(headers, rows):
    parts = ['<w:tbl><w:tblPr><w:tblStyle w:val="Normal"/>'
             '<w:tblW w:w="0" w:type="auto"/>'
             '<w:tblBorders>'
             '<w:top w:val="single" w:sz="4" w:color="8B96AB"/>'
             '<w:left w:val="single" w:sz="4" w:color="8B96AB"/>'
             '<w:bottom w:val="single" w:sz="4" w:color="8B96AB"/>'
             '<w:right w:val="single" w:sz="4" w:color="8B96AB"/>'
             '<w:insideH w:val="single" w:sz="4" w:color="8B96AB"/>'
             '<w:insideV w:val="single" w:sz="4" w:color="8B96AB"/>'
             '</w:tblBorders></w:tblPr>']
    if headers:
        parts.append("<w:tr>")
        for h in headers:
            parts.append('<w:tc><w:tcPr><w:shd w:val="clear" w:fill="0A2342"/></w:tcPr>%s</w:tc>'
                         % _paragraph(h, bold=True, color="FFFFFF"))
        parts.append("</w:tr>")
    for row in rows:
        parts.append("<w:tr>")
        for cell in row:
            parts.append("<w:tc>%s</w:tc>" % _paragraph(cell))
        parts.append("</w:tr>")
    parts.append("</w:tbl><w:p/>")
    return "".join(parts)


def create_document(path, blocks):
    """Write a .docx file from a list of block dicts (see module docstring)."""
    body = []
    for block in blocks:
        btype = block.get("type")
        if btype == "title":
            body.append(_paragraph(block["text"], style="Title"))
        elif btype == "heading":
            style = "Heading2" if block.get("level", 1) == 2 else "Heading1"
            body.append(_paragraph(block["text"], style=style))
        elif btype == "paragraph":
            body.append(_paragraph(block["text"], bold=block.get("bold", False)))
        elif btype == "bullets":
            for item in block.get("items", []):
                body.append(_bullet(item))
        elif btype == "table":
            body.append(_table(block.get("headers"), block.get("rows", [])))
        elif btype == "note":
            body.append(_paragraph(block["text"], color="8B96AB", size=18))
        else:
            raise ValueError("Unknown block type: %r" % btype)
    document = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        "<w:body>%s<w:sectPr/></w:body></w:document>" % "".join(body))
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", CONTENT_TYPES)
        z.writestr("_rels/.rels", ROOT_RELS)
        z.writestr("word/_rels/document.xml.rels", DOC_RELS)
        z.writestr("word/styles.xml", STYLES)
        z.writestr("word/document.xml", document)
    return path


def read_text(path):
    """Extract plain text from a .docx (paragraph per line)."""
    with zipfile.ZipFile(path) as z:
        xml = z.read("word/document.xml").decode("utf-8")
    paragraphs = re.findall(r"<w:p[ >].*?</w:p>|<w:p/>", xml, re.S)
    lines = []
    for p in paragraphs:
        texts = re.findall(r"<w:t[^>]*>(.*?)</w:t>", p, re.S)
        line = "".join(texts)
        line = (line.replace("&lt;", "<").replace("&gt;", ">")
                .replace("&quot;", '"').replace("&apos;", "'").replace("&amp;", "&"))
        if line:
            lines.append(line)
    return "\n".join(lines)


def replace_placeholders(path, mapping, out_path=None):
    """Replace {{placeholder}} tokens in a document created by this tool."""
    out_path = out_path or path
    with zipfile.ZipFile(path) as z:
        xml = z.read("word/document.xml").decode("utf-8")
        others = {n: z.read(n) for n in z.namelist() if n != "word/document.xml"}
    for key, value in mapping.items():
        xml = xml.replace("{{%s}}" % key, escape(str(value)))
    tmp = out_path + ".tmp"
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
        for name, data in others.items():
            z.writestr(name, data)
        z.writestr("word/document.xml", xml)
    shutil.move(tmp, out_path)
    return out_path
