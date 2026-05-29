#!/usr/bin/env python3
"""
Misbah's Magic — Reverse Engineering Document Generator
Pure Python stdlib — NO external packages needed.
Usage: python3 make_doc.py
"""
import zipfile, io, os, sys
from datetime import datetime

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "Misbah_Magic_Reverse_Engineering.docx")

# ── OOXML namespace shortcuts ────────────────────────────────────
NS = 'xmlns:wpc="http://schemas.microsoft.com/office/word/2010/wordprocessingCanvas" xmlns:cx="http://schemas.microsoft.com/office/drawing/2014/chartex" xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006" xmlns:aink="http://schemas.microsoft.com/office/drawing/2016/ink" xmlns:am3d="http://schemas.microsoft.com/office/drawing/2017/model3d" xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:oel="http://schemas.microsoft.com/office/2019/extlst" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:wp14="http://schemas.microsoft.com/office/word/2010/wordprocessingDrawing" xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" xmlns:w10="urn:schemas-microsoft-com:office:word" xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml" xmlns:w15="http://schemas.microsoft.com/office/word/2012/wordml" xmlns:w16cex="http://schemas.microsoft.com/office/word/2018/wordml/cex" xmlns:w16cid="http://schemas.microsoft.com/office/word/2016/wordml/cid" xmlns:w16="http://schemas.microsoft.com/office/word/2018/wordml" xmlns:w16sdtdh="http://schemas.microsoft.com/office/word/2020/wordml/sdtdatahash" xmlns:w16se="http://schemas.microsoft.com/office/word/2015/wordml/symex" xmlns:wpg="http://schemas.microsoft.com/office/word/2010/wordprocessingGroup" xmlns:wpi="http://schemas.microsoft.com/office/word/2010/wordprocessingInk" xmlns:wne="http://schemas.microsoft.com/office/word/2006/wordml" xmlns:wps="http://schemas.microsoft.com/office/word/2010/wordprocessingShape" mc:Ignorable="w14 w15 w16se w16cid w16 w16cex w16sdtdh wp14"'

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

# ── Document builder ─────────────────────────────────────────────
class Doc:
    def __init__(self):
        self._paras = []
        self._rid = 0

    def _p(self, style, runs, extra_pPr="", numId=None, indent=False, shading=None):
        """Build a <w:p> element string."""
        pPr = f'<w:pStyle w:val="{style}"/>' if style else ""
        if numId:
            pPr += f'<w:numPr><w:ilvl w:val="0"/><w:numId w:val="{numId}"/></w:numPr>'
        if indent:
            pPr += '<w:ind w:left="720"/>'
        if shading:
            pPr += f'<w:shd w:val="clear" w:color="auto" w:fill="{shading}"/>'
        pPr += extra_pPr
        pPr_block = f"<w:pPr>{pPr}</w:pPr>" if pPr else ""
        return f"<w:p>{pPr_block}{''.join(runs)}</w:p>"

    def _r(self, text, bold=False, italic=False, color=None, size=None,
           font="Arial", shading=None, code=False):
        """Build a <w:r> element string."""
        rPr = ""
        if code:
            font = "Courier New"
            size = size or 18
            color = color or "1E293B"
        if font:  rPr += f'<w:rFonts w:ascii="{font}" w:hAnsi="{font}"/>'
        if bold:  rPr += '<w:b/><w:bCs/>'
        if italic: rPr += '<w:i/><w:iCs/>'
        if size:  rPr += f'<w:sz w:val="{size}"/><w:szCs w:val="{size}"/>'
        if color: rPr += f'<w:color w:val="{color}"/>'
        if shading: rPr += f'<w:shd w:val="clear" w:color="auto" w:fill="{shading}"/>'
        rPr_block = f"<w:rPr>{rPr}</w:rPr>" if rPr else ""
        safe = text.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
        t_attrs = ' xml:space="preserve"' if text != text.strip() or '  ' in text else ''
        return f"<w:r>{rPr_block}<w:t{t_attrs}>{safe}</w:t></w:r>"

    def h1(self, text):
        r = self._r(text, bold=True, color="7C3AED", size=36)
        self._paras.append(self._p("MM-H1", [r]))

    def h2(self, text):
        r = self._r(text, bold=True, color="1F4E79", size=28)
        self._paras.append(self._p("MM-H2", [r]))

    def h3(self, text):
        r = self._r(text, bold=True, color="475569", size=24)
        self._paras.append(self._p("MM-H3", [r]))

    def para(self, text, bold=False, color=None):
        r = self._r(text, bold=bold, color=color, size=22)
        self._paras.append(self._p("Normal", [r]))

    def bullet(self, text):
        r = self._r(text, size=21)
        self._paras.append(self._p("Normal", [r], numId=1))

    def code(self, text):
        r = self._r(text, code=True)
        self._paras.append(self._p("Normal", [r], indent=True, shading="F1F5F9"))

    def box(self, text, bg="EDE9FE"):
        r = self._r(text, size=21)
        self._paras.append(self._p("Normal", [r], shading=bg,
            extra_pPr='<w:ind w:left="360" w:right="360"/>'
                      '<w:pBdr><w:left w:val="single" w:sz="12" w:space="4" w:color="7C3AED"/></w:pBdr>'))

    def divider(self):
        self._paras.append(
            '<w:p><w:pPr><w:pBdr><w:bottom w:val="single" w:sz="4" w:space="1" w:color="7C3AED"/></w:pBdr>'
            '<w:spacing w:before="120" w:after="120"/></w:pPr></w:p>')

    def page_break(self):
        self._paras.append('<w:p><w:r><w:br w:type="page"/></w:r></w:p>')

    def table(self, headers, rows, widths):
        """Build a simple table."""
        total = sum(widths)
        def cell(text, bg, bold=False, white=False):
            color = "FFFFFF" if white else "000000"
            rr = self._r(text, bold=bold, color=color, size=18)
            shd = f'<w:shd w:val="clear" w:color="auto" w:fill="{bg}"/>'
            tc_pr = f'<w:tcPr><w:tcW w:w="{widths[0]}" w:type="dxa"/>{shd}<w:tcMar><w:top w:w="60" w:type="dxa"/><w:bottom w:w="60" w:type="dxa"/><w:left w:w="100" w:type="dxa"/><w:right w:w="100" w:type="dxa"/></w:tcMar></w:tcPr>'
            return f'<w:tc>{tc_pr}<w:p><w:r>{rr}</w:r></w:p></w:tc>'

        tbl_pr = f'<w:tblPr><w:tblW w:w="{total}" w:type="dxa"/><w:tblBorders><w:top w:val="single" w:sz="2" w:color="CBD5E1"/><w:left w:val="single" w:sz="2" w:color="CBD5E1"/><w:bottom w:val="single" w:sz="2" w:color="CBD5E1"/><w:right w:val="single" w:sz="2" w:color="CBD5E1"/><w:insideH w:val="single" w:sz="2" w:color="CBD5E1"/><w:insideV w:val="single" w:sz="2" w:color="CBD5E1"/></w:tblBorders></w:tblPr>'
        cols = "".join(f'<w:gridCol w:w="{w}"/>' for w in widths)
        tbl = f'<w:tbl>{tbl_pr}<w:tblGrid>{cols}</w:tblGrid>'

        # Header row
        hdr_cells = []
        for i, h in enumerate(headers):
            shd = f'<w:shd w:val="clear" w:color="auto" w:fill="1F4E79"/>'
            rr = self._r(h, bold=True, color="FFFFFF", size=18)
            tc_pr = f'<w:tcPr><w:tcW w:w="{widths[i]}" w:type="dxa"/>{shd}<w:tcMar><w:top w:w="60" w:type="dxa"/><w:bottom w:w="60" w:type="dxa"/><w:left w:w="100" w:type="dxa"/><w:right w:w="100" w:type="dxa"/></w:tcMar></w:tcPr>'
            hdr_cells.append(f'<w:tc>{tc_pr}<w:p><w:r>{rr}</w:r></w:p></w:tc>')
        tbl += f'<w:tr>{"".join(hdr_cells)}</w:tr>'

        for ri, row in enumerate(rows):
            bg = "FFFFFF" if ri % 2 == 0 else "F8FAFC"
            row_cells = []
            for ci, val in enumerate(row):
                shd = f'<w:shd w:val="clear" w:color="auto" w:fill="{bg}"/>'
                rr = self._r(str(val), size=18)
                w_val = widths[ci] if ci < len(widths) else widths[-1]
                tc_pr = f'<w:tcPr><w:tcW w:w="{w_val}" w:type="dxa"/>{shd}<w:tcMar><w:top w:w="60" w:type="dxa"/><w:bottom w:w="60" w:type="dxa"/><w:left w:w="100" w:type="dxa"/><w:right w:w="100" w:type="dxa"/></w:tcMar></w:tcPr>'
                row_cells.append(f'<w:tc>{tc_pr}<w:p><w:r>{rr}</w:r></w:p></w:tc>')
            tbl += f'<w:tr>{"".join(row_cells)}</w:tr>'

        tbl += '</w:tbl>'
        self._paras.append(tbl)
        self._paras.append('<w:p/>')  # spacer after table

    def build(self):
        body = "\n".join(str(p) for p in self._paras)
        return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document {NS}>
<w:body>
{body}
<w:sectPr>
  <w:pgSz w:w="12240" w:h="15840"/>
  <w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440"/>
</w:sectPr>
</w:body>
</w:document>'''


def styles_xml():
    return '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
          xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <w:docDefaults>
    <w:rPrDefault><w:rPr>
      <w:rFonts w:ascii="Arial" w:hAnsi="Arial"/>
      <w:sz w:val="22"/><w:szCs w:val="22"/>
      <w:lang w:val="en-US"/>
    </w:rPr></w:rPrDefault>
  </w:docDefaults>
  <w:style w:type="paragraph" w:styleId="Normal">
    <w:name w:val="Normal"/>
    <w:pPr><w:spacing w:before="80" w:after="80"/></w:pPr>
    <w:rPr><w:rFonts w:ascii="Arial" w:hAnsi="Arial"/><w:sz w:val="22"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="MM-H1">
    <w:name w:val="MM-H1"/>
    <w:basedOn w:val="Normal"/>
    <w:pPr><w:outlineLvl w:val="0"/><w:spacing w:before="400" w:after="160"/></w:pPr>
    <w:rPr><w:b/><w:color w:val="7C3AED"/><w:sz w:val="36"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="MM-H2">
    <w:name w:val="MM-H2"/>
    <w:basedOn w:val="Normal"/>
    <w:pPr><w:outlineLvl w:val="1"/><w:spacing w:before="280" w:after="120"/></w:pPr>
    <w:rPr><w:b/><w:color w:val="1F4E79"/><w:sz w:val="28"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="MM-H3">
    <w:name w:val="MM-H3"/>
    <w:basedOn w:val="Normal"/>
    <w:pPr><w:outlineLvl w:val="2"/><w:spacing w:before="240" w:after="80"/></w:pPr>
    <w:rPr><w:b/><w:color w:val="475569"/><w:sz w:val="24"/></w:rPr>
  </w:style>
</w:styles>'''


def numbering_xml():
    return '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:numbering xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:abstractNum w:abstractNumId="0">
    <w:multiLevelType w:val="hybridMultilevel"/>
    <w:lvl w:ilvl="0">
      <w:start w:val="1"/>
      <w:numFmt w:val="bullet"/>
      <w:lvlText w:val="&#x2022;"/>
      <w:lvlJc w:val="left"/>
      <w:pPr><w:ind w:left="720" w:hanging="360"/></w:pPr>
      <w:rPr><w:rFonts w:ascii="Symbol" w:hAnsi="Symbol"/></w:rPr>
    </w:lvl>
  </w:abstractNum>
  <w:num w:numId="1">
    <w:abstractNumId w:val="0"/>
  </w:num>
</w:numbering>'''


def rels_xml():
    return '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>'''


def doc_rels_xml():
    return '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/settings" Target="settings.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/numbering" Target="numbering.xml"/>
</Relationships>'''


def content_types_xml():
    return '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
  <Override PartName="/word/settings.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.settings+xml"/>
  <Override PartName="/word/numbering.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.numbering+xml"/>
  <Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
  <Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
</Types>'''


def settings_xml():
    return '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:settings xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:defaultTabStop w:val="720"/>
</w:settings>'''


def core_xml():
    now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
  xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/">
  <dc:title>Misbah&#x2019;s Magic &#x2014; Reverse Engineering Document</dc:title>
  <dc:creator>Nova (AI Assistant)</dc:creator>
  <dcterms:created xsi:type="dcterms:W3CDTF" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">{now}</dcterms:created>
</cp:coreProperties>'''


def app_xml():
    return '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties">
  <Application>Microsoft Office Word</Application>
</Properties>'''


# ════════════════════════════════════════════════════════════════
#   DOCUMENT CONTENT
# ════════════════════════════════════════════════════════════════

def build_document():
    d = Doc()

    # ── COVER PAGE ───────────────────────────────────────────────
    d._paras.append('<w:p><w:pPr><w:spacing w:before="2880"/></w:pPr></w:p>')
    d._paras.append(d._p("Normal", [d._r("✨ Misbah’s Magic", bold=True, color="7C3AED", size=64)],
                         extra_pPr='<w:jc w:val="center"/>'))
    d._paras.append(d._p("Normal",
        [d._r("সম্পূর্ণ Reverse Engineering ও Technical Learning Document",
              bold=True, color="1F4E79", size=32)],
        extra_pPr='<w:jc w:val="center"/>'))
    d.divider()
    d._paras.append(d._p("Normal",
        [d._r("একটি Professional Bank Reconciliation Platform-এর", color="475569", size=24)],
        extra_pPr='<w:jc w:val="center"/>'))
    d._paras.append(d._p("Normal",
        [d._r("সম্পূর্ণ Code Audit + Beginner-Friendly শিক্ষণ ম্যানুয়াল", color="475569", size=24)],
        extra_pPr='<w:jc w:val="center"/>'))
    d._paras.append(d._p("Normal",
        [d._r("তৈরি করেছে: Nova (AI Assistant) · মে ২০২৬", color="94A3B8", size=20)],
        extra_pPr='<w:jc w:val="center"/>'))
    d.page_break()

    # ════ PART 1 ════════════════════════════════════════════════
    d.h1("PART 1 — Executive Overview: এই App কী?")
    d.divider()
    d.h2("1.1 এই App কী এবং এটা কী সমস্যা সমাধান করে?")
    d.para("Misbah’s Magic হলো একটি Professional Bank Reconciliation Platform। সহজ ভাষায়: এটা দুটো financial document মিলিয়ে দেখার একটা smart tool।")
    d.para("সমস্যাটা কী? প্রতি মাসে একজন accountant বা business owner দুটো জায়গায় transaction দেখেন:")
    d.bullet("Bank Statement — ব্যাংক থেকে আসা, যেখানে সব টাকা আসা-যাওয়ার record থাকে")
    d.bullet("QuickBooks Export — company-র নিজের accounting software থেকে নামানো record")
    d.para("এই দুটো সবসময় match করে না। Misbah’s Magic এই কাজটা seconds-এ করে দেয় — AI ব্যবহার করে, fuzzy matching ব্যবহার করে, automatically সব discrepancy খুঁজে বের করে।")
    d.h2("1.2 Core Features")
    d.bullet("Excel / CSV Reconciliation: Bank আর QuickBooks-এর Excel/CSV file upload করো, সঙ্গে সঙ্গে মিলিয়ে দেবে")
    d.bullet("AI PDF Mode: Bank statement যদি PDF হয়, Google Gemini AI সেটা পড়ে transaction বের করে আনে")
    d.bullet("Smart Matching Algorithm: Amount + Date + Description — তিনটা জিনিস মিলিয়ে match করে")
    d.bullet("Color-coded Excel Report: সব result professional Excel file হিসেবে download করা যায়")
    d.bullet("Multi-user Login: username + password দিয়ে secure access")
    d.bullet("Live Dashboard: Matched, Missing, Duplicate, Discrepancy — সব আলাদা tab-এ দেখা যায়")
    d.h2("1.3 User Journey")
    d.para("Step 1: Browser-এ app খোলে, username আর password দিয়ে login করে।")
    d.para("Step 2: Bank Statement file upload করে (Excel, CSV, বা PDF)।")
    d.para("Step 3: QuickBooks Export file upload করে (Excel বা CSV)।")
    d.para("Step 4: ‘Run Reconciliation’ button press করে।")
    d.para("Step 5: কয়েক সেকেন্ড পরে result দেখে — কতটা match হলো, কী missing, কী discrepancy।")
    d.para("Step 6: ‘Export Report’ button দিয়ে professional Excel report download করে।")
    d.h2("1.4 Real-world Analogy")
    d.box("चिন্তা করো তুমি একটা বড় দোকানের মালিক। তোমার দোকানের cashier প্রতিদিন sales লিখে রাখে। মাস শেষে ব্যাংক থেকে statement আসে। এখন তোমাকে দেখতে হবে — cashier যা লিখেছে আর ব্যাংক যা বলছে — এই দুটো মিলছে কিনা। Misbah’s Magic এই কাজটাই করে — হাজার হাজার transaction-এর জন্য, seconds-এ।", "EDE9FE")
    d.page_break()

    # ════ PART 2 ════════════════════════════════════════════════
    d.h1("PART 2 — System Architecture: পুরো System কীভাবে কাজ করে?")
    d.divider()
    d.h2("2.1 Architecture Overview")
    d.para("Misbah’s Magic একটি Client-Server architecture ব্যবহার করে। দুটো আলাদা অংশ আছে:")
    d.bullet("Frontend (Client): Browser-এ চলে — HTML, CSS, JavaScript দিয়ে তৈরি")
    d.bullet("Backend (Server): Python Flask server — logic, file processing সব এখানে হয়")
    d.h2("2.2 System Flow Diagram")
    for line in ["User Browser","    │  (HTTP Request)","    ▼","Flask Server (Python) ← port 8080","    │","    ├── /api/auth/verify       ← Login check","    ├── /api/reconcile/excel   ← Excel processing","    ├── /api/reconcile/pdf     ← PDF + AI processing","    ├── /api/reports/download  ← Report download","    └── /api/health            ← Status check","    │","    ├── pandas (data processing)","    ├── openpyxl (Excel read/write)","    └── Google Gemini API (PDF extraction)","    │","    ▼  (JSON Response)","User Browser (shows results)"]:
        d.code(line)
    d.h2("2.3 Technology Stack")
    d.table(
        ["Layer","Technology","Version","Why Used"],
        [
            ["Frontend","HTML5 + CSS3","","UI তৈরির জন্য — কোনো framework নেই"],
            ["Frontend","Vanilla JavaScript","","Lightweight, fast, no build step"],
            ["Backend","Python Flask","3.0.3","Lightweight web framework"],
            ["Backend","Flask-CORS","4.0.1","Browser cross-origin allow"],
            ["Data","pandas","2.2.2","Excel/CSV পড়া, DataFrame"],
            ["Data","openpyxl","3.1.5","Excel তৈরি (reports)"],
            ["AI","Google Gemini 1.5 Pro","0.8.3","PDF থেকে transaction extract"],
            ["Deploy","gunicorn","21.2.0","Production WSGI server"],
        ],
        [1600,2200,1200,4360]
    )
    d.page_break()

    # ════ PART 3 ════════════════════════════════════════════════
    d.h1("PART 3 — Project Structure Map: প্রতিটি ফাইল কী করে?")
    d.divider()
    d.h2("3.1 Complete Folder Tree")
    for line in [
        "misbah-magic/",
        "├── backend/                    ← Python Flask server",
        "│   ├── app.py                  ← Main entry point",
        "│   ├── config.py               ← Environment variables",
        "│   ├── .env                    ← Secrets (users, API key)",
        "│   ├── requirements.txt        ← Python packages",
        "│   └── modules/",
        "│       ├── auth/routes.py          ← /api/auth/verify",
        "│       ├── reconciliation/",
        "│       │   ├── routes.py           ← /api/reconcile/*",
        "│       │   ├── excel_engine.py     ← Excel/CSV processing",
        "│       │   ├── pdf_engine.py       ← PDF + Gemini AI",
        "│       │   └── fuzzy_matcher.py    ← Core matching algorithm",
        "│       └── reports/",
        "│           ├── routes.py           ← /api/reports/download",
        "│           └── generator.py        ← Color-coded Excel report",
        "├── frontend/",
        "│   ├── index.html              ← Single Page Application",
        "│   └── assets/",
        "│       ├── css/variables.css   ← Design tokens",
        "│       ├── css/base.css        ← CSS reset",
        "│       ├── css/animations.css  ← Animations",
        "│       ├── js/config.js        ← API URL, constants",
        "│       ├── js/api.js           ← HTTP client",
        "│       ├── js/state.js         ← State management",
        "│       ├── js/ui.js            ← DOM helpers, toast",
        "│       ├── js/uploader.js      ← Drag-drop upload",
        "│       ├── js/results.js       ← Results rendering",
        "│       └── js/app.js           ← Main entry point",
        "├── run.sh                      ← Local start script",
        "├── render.yaml                 ← Render.com deployment",
        "└── README.md                   ← Documentation",
    ]:
        d.code(line)
    d.h2("3.2 Dead Code / Unused Files")
    d.box("⚠️  IMPORTANT: backend/utils/ ফোল্ডারের সব ফাইল এবং frontend/css/style.css এবং frontend/js/ ফোল্ডারের ফাইলগুলো আর ব্যবহার হচ্ছে না। এগুলো পুরনো version-এর legacy code। Remove করা safe।", "FEF3C7")
    d.page_break()

    # ════ PART 4 ════════════════════════════════════════════════
    d.h1("PART 4 — Execution Flow: User Action থেকে Response পর্যন্ত")
    d.divider()
    d.h2("4.1 App Startup Flow")
    for line in ["python3 backend/app.py","  └── create_app() call","      ├── Flask app তৈরি","      ├── CORS enable","      ├── auth_bp → /api/auth/*","      ├── recon_bp → /api/reconcile/*","      ├── reports_bp → /api/reports/*","      └── app.run(0.0.0.0:8080)"]:
        d.code(line)
    d.h2("4.2 Login Flow")
    d.para("Step 1: Browser-এ http://localhost:8080 খোলে")
    d.para("Step 2: Flask / route index.html পাঠায়")
    d.para("Step 3: Browser JavaScript লোড করে — config.js → api.js → state.js → ui.js → uploader.js → results.js → app.js")
    d.para("Step 4: boot() function চলে → login screen দেখায়")
    d.para("Step 5: Background-এ Api.ping() দিয়ে health check")
    d.para("Step 6-7: User username+password দিয়ে Submit → POST /api/auth/verify")
    d.para("Step 8-9: config.get_users() থেকে users load → password match")
    d.para("Step 10-12: {success: true} → State.setState({authenticated: true}) → Dashboard দেখায়")
    d.h2("4.3 Excel Reconciliation — Complete Trace")
    for line in [
        "User → দুটো file select → 'Run Reconciliation' press",
        "",
        "app.js:_run()",
        "  ├── isPdf? → false (ফাইল Excel)",
        "  └── Api.reconcileExcel(bankFile, qbFile)",
        "",
        "api.js: fetch POST /api/reconcile/excel (FormData)",
        "",
        "routes.py:reconcile_excel()",
        "  ├── extension check (_allowed)",
        "  ├── temp folder-এ save (_save_upload)",
        "  └── run_excel_reconciliation()",
        "",
        "excel_engine.py:",
        "  ├── _load_file() → pandas DataFrame",
        "  ├── _build_records() → list of dicts",
        "  └── match_transactions()",
        "",
        "fuzzy_matcher.py:match_transactions():",
        "  ├── GATE 1: |amount_diff| <= 0.01",
        "  ├── GATE 2: |date_diff| <= 3 days",
        "  └── SCORE: description similarity >= 0.60",
        "",
        "generator.py:generate_excel_report()",
        "  └── Color-coded .xlsx তৈরি → report_dir",
        "",
        "JSON Response → Results.render(data) → Dashboard দেখায়",
    ]:
        d.code(line if line else " ")
    d.h2("4.4 PDF Mode (AI Flow)")
    d.code("pdf_engine.py:extract_pdf_transactions()")
    d.code("  ├── PDF → base64 encode")
    d.code("  ├── Google Gemini 1.5 Pro API call")
    d.code("  ├── Prompt: 'Extract ALL transactions as JSON array'")
    d.code("  └── JSON parse → normalized records")
    d.code("  (তারপর Excel flow-এর মতো match_transactions চলে)")
    d.page_break()

    # ════ PART 5 ════════════════════════════════════════════════
    d.h1("PART 5 — Frontend Deep Dive: UI কীভাবে তৈরি?")
    d.divider()
    d.h2("5.1 Single Page Application (SPA)")
    d.para("এই app একটিমাত্র HTML file (index.html) দিয়ে তৈরি। Page reload হয় না — JavaScript screen switch করে।")
    d.bullet("screen-login — Login form (.screen.active না হলে display:none)")
    d.bullet("screen-dashboard — মূল app (.active হলে display:flex)")
    d.h2("5.2 CSS Architecture — 4 Layer System")
    d.table(
        ["File","Purpose","Example"],
        [
            ["variables.css","Design tokens — সব রং, font, shadow","--clr-primary: #7C3AED"],
            ["base.css","CSS reset + typography","*, margin:0, padding:0"],
            ["animations.css","keyframe animations","fadeIn, popIn, shimmer"],
            ["index.html <style>","Component styles",".login-card, .upload-zone"],
        ],
        [3000,4500,3000]
    )
    d.h2("5.3 JavaScript Module Load Order")
    d.code("config.js   → API_BASE URL, APP_NAME define")
    d.code("api.js      → Api object (CONFIG ব্যবহার করে)")
    d.code("state.js    → State object (no dependency)")
    d.code("ui.js       → UI object (CONFIG ব্যবহার করে)")
    d.code("uploader.js → Uploader (UI, State ব্যবহার করে)")
    d.code("results.js  → Results (State, UI ব্যবহার করে)")
    d.code("app.js      → Entry point (সবগুলো ব্যবহার করে)")
    d.para("প্রতিটি file একটি IIFE (Immediately Invoked Function Expression) — নিজেই চলে এবং একটা public object return করে।")
    d.h2("5.4 State Management (state.js)")
    d.para("React-এর মতোই, কিন্তু vanilla JavaScript-এ। Observer pattern ব্যবহার করে।")
    d.code("State properties:")
    d.code("  authenticated: false   ← Login হয়েছে কিনা")
    d.code("  activeTab:     'matched'← কোন tab active")
    d.code("  loading:       false   ← Processing চলছে কিনা")
    d.code("  results:       null    ← API থেকে আসা data")
    d.code("  reportFilename:null    ← Download filename")
    d.code("  bankFile:      null    ← Selected bank file")
    d.code("  qbFile:        null    ← Selected QB file")
    d.code("  searchQuery:   ''      ← Search text")
    d.h2("5.5 Results Rendering (results.js)")
    d.table(
        ["Tab","Data","Columns"],
        [
            ["matched","data.matched[]","Date, Desc, Bank Amt, QB Amt, Similarity"],
            ["missing_in_qb","data.missing_in_qb[]","Date, Desc, Amount, Note"],
            ["missing_in_bank","data.missing_in_bank[]","Date, Desc, Amount, Note"],
            ["discrepancies","data.discrepancies[]","Date, Desc, Bank Amt, QB Amt, Diff"],
            ["duplicates","data.duplicates[]","Date, Desc, Amount, Occurrences"],
        ],
        [2400,3200,4000]
    )
    d.page_break()

    # ════ PART 6 ════════════════════════════════════════════════
    d.h1("PART 6 — Backend Deep Dive: Server Logic")
    d.divider()
    d.h2("6.1 Flask Application Factory Pattern")
    d.code("create_app() এর কাজ:")
    d.code("1. frontend_dir = ../frontend path নির্ধারণ")
    d.code("2. Flask(static_folder=frontend_dir)")
    d.code("3. CORS(app) — browser cross-origin allow")
    d.code("4. Blueprints register")
    d.code("5. / route = index.html")
    d.code("6. /api/health = status JSON")
    d.h2("6.2 Blueprint Architecture")
    d.table(
        ["Blueprint","URL Prefix","File","Purpose"],
        [
            ["auth_bp","/api/auth","modules/auth/","Login verification"],
            ["recon_bp","/api/reconcile","modules/reconciliation/","File processing"],
            ["reports_bp","/api/reports","modules/reports/","File download"],
        ],
        [2200,2400,3200,2160]
    )
    d.h2("6.3 Configuration (config.py)")
    d.table(
        ["Variable","Default","Purpose"],
        [
            ["USERS","misbah:misbah2024","username:password, comma-separated"],
            ["GEMINI_API_KEY","","Google Gemini API key"],
            ["PORT","8080","Server port"],
            ["AMOUNT_TOLERANCE","0.01","Amount match tolerance ($0.01)"],
            ["DATE_TOLERANCE_DAYS","3","Date match tolerance (3 days)"],
            ["SIMILARITY_THRESHOLD","0.60","Min description similarity (60%)"],
        ],
        [3000,2600,4760]
    )
    d.h2("6.4 Error Handling Pattern")
    d.code("try:")
    d.code("    result = run_excel_reconciliation(bank_path, qb_path)")
    d.code("    return jsonify(result)")
    d.code("except Exception as exc:")
    d.code("    return jsonify({'error': str(exc)}), 500")
    d.code("finally:")
    d.code("    _cleanup(bank_path, qb_path)  ← সবসময় cleanup")
    d.para("finally block নিশ্চিত করে যে error হলেও temp files delete হবে।")
    d.page_break()

    # ════ PART 7 ════════════════════════════════════════════════
    d.h1("PART 7 — Core Algorithm: Fuzzy Matching Deep Dive")
    d.divider()
    d.h2("7.1 Fuzzy Matching কী?")
    d.para("Fuzzy matching মানে exact match না হলেও 'কাছাকাছি' match খোঁজা।")
    d.bullet("Bank: 'AMAZON.COM PAYMENT' → QB: 'Amazon Purchase' — এগুলো same transaction")
    d.bullet("Bank amount: $100.00 → QB: $100.01 — rounding difference হতে পারে")
    d.bullet("Bank date: Jan 5 → QB: Jan 7 — posting date আর transaction date আলাদা")
    d.h2("7.2 normalize_amount()")
    d.code("'$1,234.56' → 1234.56")
    d.code("'(500.00)'  → -500.00  (নেগেটিভ হিসাব)")
    d.code("'£100'      → 100.0")
    d.code("re.sub(r'[,$£€\\s]', '', str(value))  — currency symbols remove")
    d.code(".replace('(', '-')  — accounting notation নেগেটিভ")
    d.h2("7.3 text_similarity()")
    d.para("Python-এর difflib.SequenceMatcher ব্যবহার করে। 0.0 থেকে 1.0 উপর ratio দেয়।")
    d.code("text_similarity('amazon', 'amazon')  → 1.0  (100%)")
    d.code("text_similarity('amazon', 'amaz0n')  → 0.91 (91%)")
    d.code("text_similarity('amazon', 'paypal')  → 0.21 (21%)")
    d.h2("7.4 match_transactions() — Core Algorithm")
    d.code("প্রতিটি bank transaction এর জন্য (outer loop O(n)):")
    d.code("  প্রতিটি QB transaction এর জন্য (inner loop O(m)):")
    d.code("    GATE 1: |bank_amount - qb_amount| > 0.01 → SKIP")
    d.code("    GATE 2: |bank_date - qb_date| > 3 days → SKIP")
    d.code("    SCORE: text_similarity() → best score track")
    d.code("")
    d.code("  best_score >= 0.60:")
    d.code("    → matched[] এ add")
    d.code("    → qb_consumed[best_idx] = True (পরে আর use নয়)")
    d.code("")
    d.code("শেষে:")
    d.code("  missing_in_qb  = bank যেগুলো matched=False")
    d.code("  missing_in_bank= QB যেগুলো consumed=False")
    d.code("  duplicates     = bank-এ same amount+desc একের বেশি")
    d.h2("7.5 Configuration Tuning")
    d.box("AMOUNT_TOLERANCE=0.01  → $0.01 difference allow (rounding)\nDATE_TOLERANCE_DAYS=3   → 3 দিনের পার্থক্য allow (posting delays)\nSIMILARITY_THRESHOLD=0.60 → 60% similarity minimum", "D1FAE5")
    d.page_break()

    # ════ PART 8 ════════════════════════════════════════════════
    d.h1("PART 8 — Authentication & Security")
    d.divider()
    d.h2("8.1 Authentication System")
    d.code("Login Flow:")
    d.code("1. POST /api/auth/verify")
    d.code("   Body: {username: 'misbah', password: 'misbah2024'}")
    d.code("2. config.get_users() → {'misbah': 'misbah2024'}")
    d.code("3. users.get(username) == password → True")
    d.code("4. {success: true} return")
    d.code("5. State.setState({authenticated: true})")
    d.para("Server-side কোনো session নেই। Authentication শুধু frontend state-এ থাকে।")
    d.h2("8.2 Multi-user Support")
    d.code(".env ফাইলে:")
    d.code("USERS=misbah:misbah2024,client1:pass123,acc:securepass")
    d.para("get_users() এটাকে parse করে {username: password} dict বানায়।")
    d.h2("8.3 Security Vulnerabilities")
    d.box("⚠️  KNOWN ISSUES:", "FEE2E2")
    d.bullet("Passwords are plaintext — .env-এ plain text, hash করা নেই")
    d.bullet("No session management — JWT token নেই")
    d.bullet("No rate limiting — brute force possible")
    d.bullet("GEMINI_API_KEY .env-এ — git push হলে exposed")
    d.bullet("No CSRF protection")
    d.h2("8.4 Security Fix Recommendations")
    d.bullet("Password hashing: bcrypt বা argon2 ব্যবহার করো")
    d.bullet("JWT tokens: Flask-JWT-Extended দিয়ে token system")
    d.bullet("Rate limiting: Flask-Limiter package")
    d.bullet("HTTPS: Render.com production-এ automatically দেয়")
    d.bullet(".gitignore: .env সবসময় gitignore-এ (স্করা আছে)")
    d.h2("8.5 File Upload Security")
    d.bullet("secure_filename() — directory traversal attack prevent")
    d.bullet("Extension whitelist — শুধু xlsx, xls, csv, pdf allow")
    d.bullet("UUID prefix — filename collision prevent")
    d.bullet("Temp cleanup — files permanent থাকে না")
    d.bullet("os.path.basename() — download endpoint path traversal prevent")
    d.page_break()

    # ════ PART 9 ════════════════════════════════════════════════
    d.h1("PART 9 — API System Deep Dive")
    d.divider()
    d.h2("9.1 All API Endpoints")
    d.table(
        ["Endpoint","Method","Input","Output"],
        [
            ["POST /api/auth/verify","POST","JSON: username, password","JSON: {success: true/false}"],
            ["POST /api/reconcile/excel","POST","FormData: bank_file, qb_file","JSON: full result + report_filename"],
            ["POST /api/reconcile/pdf","POST","FormData: pdf_file, qb_file","JSON: full result + extracted_count"],
            ["GET /api/reports/download/<fn>","GET","URL param: filename","File (.xlsx) download"],
            ["GET /api/health","GET","None","JSON: {status: 'ok'}"],
            ["GET /","GET","None","index.html (frontend)"],
        ],
        [3600,1200,2500,3060]
    )
    d.h2("9.2 Complete API Response Structure")
    d.code("{")
    d.code("  'source': 'excel' | 'pdf',")
    d.code("  'matched': [{bank_description, qb_description,")
    d.code("    bank_date, qb_date, bank_amount, qb_amount, similarity}],")
    d.code("  'missing_in_qb': [{description, date, amount}],")
    d.code("  'missing_in_bank': [{description, date, amount}],")
    d.code("  'duplicates': [{description, date, amount}],")
    d.code("  'discrepancies': [{bank_description, qb_description,")
    d.code("    bank_date, qb_date, bank_amount, qb_amount, difference}],")
    d.code("  'summary': {total_bank, total_qb, matched_count,")
    d.code("    missing_in_qb_count, missing_in_bank_count,")
    d.code("    duplicates_count, discrepancies_count},")
    d.code("  'report_filename': 'report_a1b2c3d4.xlsx'")
    d.code("}")
    d.h2("9.3 API Client (api.js)")
    d.para("api.js একটা Module Pattern (IIFE) ব্যবহার করে। সব HTTP calls এখানে centralized:")
    d.bullet("verifyPassword(username, password) — POST /api/auth/verify")
    d.bullet("reconcileExcel(bankFile, qbFile) — POST /api/reconcile/excel")
    d.bullet("reconcilePdf(pdfFile, qbFile) — POST /api/reconcile/pdf")
    d.bullet("reportUrl(filename) — GET URL builder")
    d.bullet("ping() — GET /api/health (3s timeout)")
    d.page_break()

    # ════ PART 10 ════════════════════════════════════════════════
    d.h1("PART 10 — Deployment & DevOps")
    d.divider()
    d.h2("10.1 Local Development")
    d.code("1. git clone <repo-url>")
    d.code("2. cd misbah-magic/backend")
    d.code("3. pip install -r requirements.txt")
    d.code("4. cp .env.example .env  (তারপর values fill করো)")
    d.code("5. python app.py")
    d.code("6. Browser: http://localhost:8080")
    d.para("অথবা root folder থেকে: bash run.sh (auto-install করে)")
    d.h2("10.2 Render.com Deployment Config")
    d.code("render.yaml:")
    d.code("  type: web")
    d.code("  buildCommand: pip install -r backend/requirements.txt")
    d.code("  startCommand: cd backend && gunicorn 'app:create_app()'")
    d.code("  envVars: USERS, GEMINI_API_KEY, PORT")
    d.para("Render.com automatically HTTPS, custom domain, auto-deploy from GitHub দেয়।")
    d.h2("10.3 gunicorn vs Flask dev server")
    d.bullet("Flask dev server: single-threaded, একটাই request handle")
    d.bullet("gunicorn: multi-worker, অনেক users একসাথে handle")
    d.bullet("gunicorn: WSGI standard, production-ready")
    d.h2("10.4 Environment Variables")
    d.bullet("Local: .env file (gitignore-এ আছে — GitHub-এ যায় না)")
    d.bullet("Production (Render): Dashboard-এ manually set")
    d.bullet("Team: .env.example থেকে copy করে values দাও")
    d.box("⚠️  Upload আর Report files temp directory-তে থাকে। Render.com-এ restart-এ files মুছে যাবে। Production-এ AWS S3 ব্যবহার করা উচিত।", "FEF3C7")
    d.page_break()

    # ════ PARTS 11-15 ════════════════════════════════════════════
    d.h1("PART 11 — Packages & Dependencies")
    d.divider()
    d.table(
        ["Package","Version","Purpose","Used For"],
        [
            ["flask","3.0.3","Python web framework","HTTP server, routing, Blueprint"],
            ["flask-cors","4.0.1","Cross-Origin allow","Browser API calls"],
            ["python-dotenv","1.0.1",".env file load","Secrets management"],
            ["pandas","2.2.2","Data analysis","Excel/CSV read, DataFrame"],
            ["openpyxl","3.1.5","Excel handler","Read Excel + create reports"],
            ["google-generativeai","0.8.3","Gemini AI client","PDF transaction extract"],
            ["gunicorn","21.2.0","WSGI server","Production deployment"],
        ],
        [2400,1400,3200,3000]
    )
    d.h2("11.1 pandas কী এবং কেন?")
    d.code("pd.read_excel(path, engine='openpyxl') → DataFrame")
    d.code("df.dropna(how='all') → empty rows remove")
    d.code("pd.to_datetime(date, errors='coerce') → datetime object")
    d.code("  errors='coerce': invalid date → NaT (Not a Time)")
    d.h2("11.2 difflib.SequenceMatcher")
    d.code("SequenceMatcher(None, str_a, str_b).ratio()")
    d.code("  → 2*M / T  (M=matches, T=total chars)")
    d.code("  → সবচেয়ে বেশি মিলে যাওয়া লর্ড common subsequence")
    d.h2("11.3 openpyxl Report Features")
    d.bullet("PatternFill — cell background color")
    d.bullet("Font — bold, color, size, font family")
    d.bullet("Alignment — center, left, wrap text")
    d.bullet("Border — cell borders")
    d.bullet("merge_cells — cells merge")
    d.bullet("freeze_panes = 'A2' — header row fixed")
    d.page_break()

    d.h1("PART 12 — Performance & Optimization")
    d.divider()
    d.h2("12.1 Current Bottlenecks")
    d.bullet("Fuzzy Matching O(n×m): 1000 bank × 1000 QB = 1 million comparisons")
    d.bullet("Sequential Processing: synchronous, একটার পর একটা")
    d.bullet("PDF AI Latency: Gemini API call 5-15 seconds")
    d.bullet("No Caching: একই file দুইবার দুইবার full processing")
    d.h2("12.2 Optimization Suggestions")
    d.bullet("Amount-based pre-filtering: same amount-এর QB খুঁজে comparison কমাও")
    d.bullet("pandas vectorization: row-by-row loop এর বদলে vectorized operations")
    d.bullet("Background tasks: Celery বা Threading দিয়ে async processing")
    d.bullet("RAM: 50MB Excel → ~200-500MB RAM। Render.com free tier = 512MB")
    d.page_break()

    d.h1("PART 13 — Tech Debt & Code Quality")
    d.divider()
    d.h2("13.1 Dead Code")
    d.bullet("backend/utils/ — পুরনো version, modules/ দিয়ে replace হয়েছে")
    d.bullet("frontend/css/style.css — assets/css/ দিয়ে replace")
    d.bullet("frontend/js/api.js, app.js — assets/js/ দিয়ে replace")
    d.h2("13.2 Missing")
    d.bullet("File size enforcement — config-এ আছে কিন্তু enforce হচ্ছে না")
    d.bullet("No logging system — Python logging module দরকার")
    d.bullet("No unit tests — pytest দিয়ে test লেখা উচিত")
    d.bullet("README outdated — single password system describe করছে")
    d.h2("13.3 Good Code Quality")
    d.bullet("Clear module separation: auth, reconciliation, reports আলাদা")
    d.bullet("Consistent error handling: try/except/finally")
    d.bullet("Security: secure_filename, basename, extension whitelist")
    d.bullet("Config centralization: সব settings config.py-তে")
    d.bullet("Frontend modularity: 7টি focused JS modules")
    d.bullet("Observer pattern: State management elegant")
    d.page_break()

    d.h1("PART 14 — Modify & Extend Guide")
    d.divider()
    d.h2("14.1 নতুন Backend Module যোগ করা")
    d.code("1. mkdir backend/modules/newfeature")
    d.code("2. __init__.py: Blueprint('newfeature', url_prefix='/api/new')")
    d.code("3. routes.py: @newfeature_bp.route('/list') ...")
    d.code("4. app.py-তে: from modules.newfeature import bp")
    d.code("             app.register_blueprint(bp)")
    d.h2("14.2 নতুন User যোগ করা")
    d.code(".env ফাইলে:")
    d.code("USERS=misbah:misbah2024,newuser:newpass123")
    d.code("Server restart করো।")
    d.h2("14.3 Matching Algorithm Tune")
    d.code("AMOUNT_TOLERANCE=0.05    ← $0.05 পর্যন্ত match")
    d.code("DATE_TOLERANCE_DAYS=7    ← 7 দিন পর্যন্ত match")
    d.code("SIMILARITY_THRESHOLD=0.50 ← 50% similarity match")
    d.page_break()

    d.h1("PART 15 — Beginner Learning Curriculum")
    d.divider()
    d.h2("15.1 এই App থেকে যা শিখলে")
    d.h3("Web Application Architecture")
    d.bullet("Client-Server model: browser আর server আলাদা")
    d.bullet("HTTP request/response cycle: সব data JSON format-এ")
    d.bullet("REST API: URL দিয়ে resources identify করা")
    d.bullet("CORS: browser security model")
    d.h3("Python Backend")
    d.bullet("Flask: lightweight web framework কীভাবে কাজ করে")
    d.bullet("Blueprint: বড় app কে modules-এ ভাগ করা")
    d.bullet("Environment variables: secrets safely manage")
    d.bullet("Error handling: try/except/finally")
    d.h3("Data Processing")
    d.bullet("pandas DataFrame: tabular data handle")
    d.bullet("Column auto-detection: heuristic algorithms")
    d.bullet("String normalization: comparison-এর আগে data clean")
    d.bullet("Fuzzy matching: approximate match")
    d.h3("Frontend JavaScript")
    d.bullet("Module pattern (IIFE): encapsulation")
    d.bullet("Observer pattern: State management")
    d.bullet("Event handling: click, change, drag")
    d.bullet("Fetch API: modern HTTP requests")
    d.h2("15.2 Programming Concepts Glossary")
    d.table(
        ["Concept","সহজ বাংলায়","App Example"],
        [
            ["API","দুটো program-এর কথা বলার নিয়ম","POST /api/reconcile/excel"],
            ["JSON","Data exchange format",'{"success": true}'],
            ["Blueprint","App-এর অংশ আলাদা করা","auth_bp, recon_bp"],
            ["CORS","Browser cross-origin security","Flask-CORS middleware"],
            ["Fuzzy Match","Exact না হলেও কাছাকাছি","SequenceMatcher ratio"],
            ["State","App-এর current condition","authenticated, loading"],
            ["Observer","Change হলে notify","State.subscribe()"],
            ["IIFE","নিজেই চলে এমন function","(() => { ... })()"],
        ],
        [2400,4000,4400]
    )
    d.h2("15.3 Next Steps")
    d.bullet("Authentication: Flask-JWT-Extended দিয়ে token system")
    d.bullet("Database: SQLite/PostgreSQL দিয়ে history store")
    d.bullet("Testing: pytest দিয়ে unit tests")
    d.bullet("React/Vue: modern frontend framework")
    d.bullet("Docker: containerize করা")
    d.bullet("CI/CD: GitHub Actions auto-deploy")
    d.page_break()

    # ════ APPENDIX ════════════════════════════════════════════════
    d.h1("APPENDIX — File-by-File Ultra Deep Breakdown")
    d.divider()
    d.h2("A1. backend/app.py")
    d.code("Line 5: import os — file path manipulation")
    d.code("Line 6: from flask import Flask, send_from_directory, jsonify")
    d.code("  Flask: web app class")
    d.code("  send_from_directory: static file serve")
    d.code("  jsonify: Python dict → JSON HTTP response")
    d.code("Line 7: CORS(app) — সব origins থেকে request allow")
    d.code("  Production-এ origins=['https://yourdomain.com'] দিতে হবে")
    d.code("Line 12: os.path.abspath() — relative → absolute path")
    d.code("Line 13: Flask(static_url_path='') — /filename → frontend/filename")
    d.code("Line 37-40: if __name__ == '__main__':")
    d.code("  → python app.py directly হলে চলে")
    d.code("  → gunicorn দিয়ে হলে চলে না")
    d.h2("A2. backend/config.py")
    d.code("load_dotenv() — .env file থেকে env vars সেট")
    d.code("get_users() — 'misbah:pass,bob:p2' → {'misbah':'pass','bob':'p2'}")
    d.code("  split(':', 1): maxsplit=1 → password-এ ':' থাকলেও ঠিক")
    d.code("  username.lower(): case insensitive login")
    d.code("FRONTEND_DIR = os.path.join(__file__, '../..', 'frontend')")
    d.code("config = Config() — Singleton instance, সব module import করে")
    d.h2("A3. modules/auth/routes.py")
    d.code("@auth_bp.route('/verify', methods=['POST'])")
    d.code("  → auth_bp prefix + /verify = /api/auth/verify")
    d.code("  → POST only, GET হলে 405 Method Not Allowed")
    d.code("request.get_json(silent=True) or {}")
    d.code("  silent=True: parse error → None (না crash)")
    d.code("  or {}: None হলে empty dict")
    d.code("users.get(username) == password: plaintext comparison")
    d.code("  → bcrypt.checkpw() ব্যবহার করা উচিত")
    d.h2("A4. modules/reconciliation/fuzzy_matcher.py")
    d.code("normalize_amount(value):")
    d.code("  pd.isna() check → 0.0 return")
    d.code("  re.sub(r'[,$£€\\s]','',str(value)): symbols remove")
    d.code("  .replace('(','-'): (100) → -100")
    d.code("  round(float(cleaned), 2): 2 decimal places")
    d.code("")
    d.code("auto_detect_columns(df):")
    d.code("  date keywords: 'date','trans date','posting date'...")
    d.code("  desc keywords: 'description','memo','narration','payee'...")
    d.code("  amount keywords: 'amount','credit','debit'...")
    d.code("  First match wins — ambiguous columns সাবধান")
    d.code("")
    d.code("match_transactions():")
    d.code("  qb_consumed = [False]*len(qb): each QB used once only")
    d.code("  O(n×m) nested loop: outer=bank, inner=QB")
    d.code("  Three gates → score → best_idx track")
    d.code("  score >= 0.60 → matched, consumed=True")
    d.h2("A5. modules/reconciliation/pdf_engine.py")
    d.code("_EXTRACTION_PROMPT:")
    d.code("  'Return ONLY a valid JSON array'")
    d.code("  Credits = positive, Debits = negative")
    d.code("  ISO 8601 dates (YYYY-MM-DD)")
    d.code("")
    d.code("extract_pdf_transactions():")
    d.code("  Lazy import: google.generativeai Python 3.14 incompatible")
    d.code("  PDF → base64 encode → Gemini API send")
    d.code("  Markdown fence strip (```json...```)")
    d.code("  json.loads() → Python list")
    d.h2("A6. modules/reports/generator.py")
    d.code("Color palette:")
    d.code("  matched='C6EFCE'(green), missing='FFC7CE'(red)")
    d.code("  discrepancy='FFEB9C'(yellow), duplicate='FCE4D6'(orange)")
    d.code("")
    d.code("_autofit(ws): column max len + 4, capped at 55")
    d.code("generate_excel_report():")
    d.code("  openpyxl.Workbook() → Summary + 5 sheets")
    d.code("  report_{uuid8}.xlsx → unique filename")
    d.code("  ws.freeze_panes='A2' → header fixed")
    d.h2("A7. frontend/assets/js/app.js")
    d.code("(async () => { ... })()")
    d.code("  IIFE + async → top-level await সম্ভব")
    d.code("")
    d.code("$ = id => document.getElementById(id)")
    d.code("  jQuery-inspired shorthand")
    d.code("")
    d.code("checkBackend(): setInterval(30_000)")
    d.code("  30_000: ES2021 numeric separator")
    d.code("  green/red dot: DOM update")
    d.code("")
    d.code("handleLogin(e):")
    d.code("  e.preventDefault(): form submit page reload prevent")
    d.code("  disabled=true: double-click prevent")
    d.code("")
    d.code("_run():")
    d.code("  isPdf = .endsWith('.pdf')")
    d.code("  isPdf ? reconcilePdf() : reconcileExcel()")
    d.code("  Auto-routing: user manually mode select করতে হয় না")
    d.h2("A8. frontend/assets/js/state.js")
    d.code("subscribe(keys, fn):")
    d.code("  keys-এর যেকোনো change হলে fn() call")
    d.code("  returns unsubscribe function")
    d.code("")
    d.code("setState(patch):")
    d.code("  patch দিয়ে state merge")
    d.code("  changed keys-এর subscribers notify")
    d.code("  same value হলে notify না")
    d.code("")
    d.code("get(key):")
    d.code("  key undefined → full state copy return")

    d.divider()
    d._paras.append(d._p("Normal",
        [d._r("✨ Document Complete — Misbah’s Magic Full Reverse Engineering",
              bold=True, color="7C3AED", size=24)],
        extra_pPr='<w:jc w:val="center"/>'))
    d._paras.append(d._p("Normal",
        [d._r("তৈরি করেছে Nova · মে ২০২৬", color="94A3B8", size=20)],
        extra_pPr='<w:jc w:val="center"/>'))

    return d.build()


# ════════════════════════════════════════════════════════════════
#   PACKAGE INTO .docx (ZIP)
# ════════════════════════════════════════════════════════════════

def create_docx(output_path):
    doc_xml = build_document()
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('[Content_Types].xml', content_types_xml())
        zf.writestr('_rels/.rels', rels_xml())
        zf.writestr('word/document.xml', doc_xml)
        zf.writestr('word/styles.xml', styles_xml())
        zf.writestr('word/numbering.xml', numbering_xml())
        zf.writestr('word/settings.xml', settings_xml())
        zf.writestr('word/_rels/document.xml.rels', doc_rels_xml())
        zf.writestr('docProps/core.xml', core_xml())
        zf.writestr('docProps/app.xml', app_xml())
    size = os.path.getsize(output_path) / 1024
    print(f"\n✨ Document saved: {output_path}")
    print(f"📊 Size: {size:.1f} KB\n")
    # Try to open the file
    try:
        import subprocess
        subprocess.Popen(['open', output_path])
        print("📄 Opening document...")
    except Exception:
        pass


if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else OUT
    print("\n✨ Generating Misbah's Magic Reverse Engineering Document...")
    print("🔧 Pure Python stdlib — no packages needed\n")
    create_docx(out)
