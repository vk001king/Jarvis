"""Create safe, editable Office files for research and study workflows."""
from __future__ import annotations

import csv
import itertools
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


_FORMAT_EXTENSIONS = {
    "word": ".docx",
    "docx": ".docx",
    "excel": ".xlsx",
    "xlsx": ".xlsx",
    "powerpoint": ".pptx",
    "ppt": ".pptx",
    "pptx": ".pptx",
}
_MAX_TEXT = 100_000
_MAX_TABLES = 20
_MAX_ROWS = 5_000
_MAX_COLUMNS = 40
_MAX_SLIDES = 100


def _text(value, label: str, limit: int = _MAX_TEXT) -> str:
    if value is None:
        return ""
    if not isinstance(value, (str, int, float)):
        raise ValueError(f"{label} must be text.")
    result = str(value).strip()
    if len(result) > limit:
        raise ValueError(f"{label} exceeds the {limit:,}-character limit.")
    return result


def _string_list(values, label: str, maximum: int) -> list[str]:
    if values is None:
        return []
    if not isinstance(values, list):
        raise ValueError(f"{label} must be a list.")
    if len(values) > maximum:
        raise ValueError(f"{label} can contain at most {maximum} items.")
    return [_text(value, label, 4_000) for value in values]


def _sections(values) -> list[dict[str, str]]:
    if values is None:
        return []
    if not isinstance(values, list) or len(values) > 60:
        raise ValueError("sections must be a list of at most 60 items.")
    result = []
    for item in values:
        if not isinstance(item, dict):
            raise ValueError("Each section must include a heading and body.")
        heading = _text(item.get("heading"), "Section heading", 300)
        body = _text(item.get("body"), "Section body")
        if heading or body:
            result.append({"heading": heading, "body": body})
    return result


def _tables(values) -> list[dict]:
    if values is None:
        return []
    if not isinstance(values, list) or len(values) > _MAX_TABLES:
        raise ValueError(f"tables must be a list of at most {_MAX_TABLES} items.")
    result = []
    for item in values:
        if not isinstance(item, dict):
            raise ValueError("Each table must include headers and rows.")
        headers = _string_list(item.get("headers"), "Table headers", _MAX_COLUMNS)
        rows = item.get("rows") or []
        if not headers:
            raise ValueError("Every table needs at least one header.")
        if not isinstance(rows, list) or len(rows) > _MAX_ROWS:
            raise ValueError(f"Each table can contain at most {_MAX_ROWS:,} rows.")
        normalized_rows = []
        for row in rows:
            if not isinstance(row, (list, tuple)) or len(row) > len(headers):
                raise ValueError("Table rows must be arrays no wider than their headers.")
            normalized_rows.append(list(row) + [""] * (len(headers) - len(row)))
        result.append({
            "title": _text(item.get("title"), "Table title", 300),
            "headers": headers,
            "rows": normalized_rows,
        })
    return result


def _slides(values) -> list[dict]:
    if values is None:
        return []
    if not isinstance(values, list) or len(values) > _MAX_SLIDES:
        raise ValueError(f"slides must be a list of at most {_MAX_SLIDES} items.")
    result = []
    for item in values:
        if not isinstance(item, dict):
            raise ValueError("Each slide must be an object.")
        result.append({
            "title": _text(item.get("title"), "Slide title", 300),
            "body": _text(item.get("body"), "Slide body", 8_000),
            "bullets": _string_list(item.get("bullets"), "Slide bullets", 30),
        })
    return result


def _image_paths(values) -> list[Path]:
    raw_paths = _string_list(values, "image_paths", 12)
    paths = []
    for raw in raw_paths:
        path = Path(raw).expanduser()
        if not path.is_file():
            raise ValueError(f"Image file not found: {raw}")
        if path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tif", ".tiff"}:
            raise ValueError(f"Unsupported image format: {path.suffix or '(none)'}")
        paths.append(path.resolve())
    return paths


def _sources(values) -> list[str]:
    return _string_list(values, "sources", 100)


def _safe_cell(value):
    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        if isinstance(value, float) and not math.isfinite(value):
            return None
        return value
    text = _text(value, "Table cell", 8_000)
    numeric = re.fullmatch(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)", text)
    if numeric:
        try:
            number = float(text)
            if math.isfinite(number):
                return int(number) if number.is_integer() else number
        except ValueError:
            pass
    if text.lstrip().startswith(("=", "+", "-", "@")):
        return "'" + text
    return text


def _slug(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("._-")
    return slug[:80] or "JARVIS_Research"


def _output_path(raw: str, title: str, suffix: str, source_path: str = "") -> Path:
    default_dir = Path.home() / "Documents" / "JARVIS Office"
    if raw:
        candidate = Path(raw).expanduser()
        if not candidate.is_absolute():
            candidate = default_dir / candidate
        if candidate.exists() and candidate.is_dir():
            candidate = candidate / f"{_slug(title)}{suffix}"
        elif not candidate.suffix:
            candidate = candidate.with_suffix(suffix)
        elif candidate.suffix.lower() != suffix:
            raise ValueError(f"Output path must use the {suffix} extension.")
    elif source_path:
        source = Path(source_path).expanduser()
        candidate = source.with_name(f"{source.stem}_JARVIS_edited{suffix}")
    else:
        candidate = default_dir / f"{_slug(title)}{suffix}"

    candidate.parent.mkdir(parents=True, exist_ok=True)
    base = candidate
    index = 2
    while candidate.exists():
        candidate = base.with_name(f"{base.stem}_{index}{base.suffix}")
        index += 1
    return candidate


def _save_new_file(path: Path, writer) -> None:
    descriptor, temp_name = tempfile.mkstemp(
        prefix=f".{path.stem}_", suffix=path.suffix, dir=str(path.parent)
    )
    os.close(descriptor)
    temp_path = Path(temp_name)
    created_target = False
    try:
        writer(temp_path)
        with temp_path.open("rb") as source, path.open("xb") as target:
            created_target = True
            shutil.copyfileobj(source, target)
            target.flush()
            os.fsync(target.fileno())
    except Exception:
        if created_target:
            try:
                path.unlink()
            except OSError:
                pass
        raise
    finally:
        try:
            temp_path.unlink()
        except FileNotFoundError:
            pass


def _load_source_table(raw_path: str) -> dict:
    source = Path(raw_path).expanduser()
    if not source.is_file():
        raise ValueError(f"Dataset file not found: {raw_path}")
    suffix = source.suffix.lower()
    if suffix == ".csv":
        with source.open("r", encoding="utf-8-sig", newline="") as stream:
            rows = list(itertools.islice(csv.reader(stream), _MAX_ROWS + 1))
    elif suffix == ".xlsx":
        from openpyxl import load_workbook

        workbook = load_workbook(source, read_only=True, data_only=True)
        try:
            worksheet = workbook.active
            rows = [
                list(row)
                for row in worksheet.iter_rows(
                    max_row=_MAX_ROWS + 1,
                    max_col=_MAX_COLUMNS,
                    values_only=True,
                )
            ]
        finally:
            workbook.close()
    else:
        raise ValueError("Dataset import supports .csv and .xlsx files.")

    rows = [row for row in rows if any(value not in (None, "") for value in row)]
    if not rows:
        raise ValueError("The selected dataset is empty.")
    raw_headers = rows[0][:_MAX_COLUMNS]
    headers = [
        _text(value, "Dataset header", 300) or f"Column {index + 1}"
        for index, value in enumerate(raw_headers)
    ]
    data = []
    for row in rows[1:_MAX_ROWS + 1]:
        values = list(row[:len(headers)])
        values.extend([""] * (len(headers) - len(values)))
        data.append(values)
    return {"title": source.stem, "headers": headers, "rows": data}


def _write_word(path: Path, title: str, content: str, sections: list[dict],
                tables: list[dict], images: list[Path], sources: list[str],
                source_path: str = "") -> None:
    from docx import Document
    from docx.shared import Inches, Pt

    document = Document(source_path) if source_path else Document()
    document.core_properties.title = title
    document.styles["Normal"].font.name = "Aptos"
    document.styles["Normal"].font.size = Pt(10)
    if source_path:
        document.add_page_break()
    document.add_heading(title, 0)
    if content:
        for paragraph in content.splitlines():
            if paragraph.strip():
                document.add_paragraph(paragraph.strip())
    for section in sections:
        if section["heading"]:
            document.add_heading(section["heading"], level=1)
        for paragraph in section["body"].splitlines():
            if paragraph.strip():
                document.add_paragraph(paragraph.strip())
    for table in tables:
        if table["title"]:
            document.add_heading(table["title"], level=2)
        word_table = document.add_table(rows=1, cols=len(table["headers"]))
        word_table.style = "Table Grid"
        for cell, header in zip(word_table.rows[0].cells, table["headers"]):
            cell.text = header
        for row in table["rows"]:
            cells = word_table.add_row().cells
            for cell, value in zip(cells, row):
                cell.text = str(_safe_cell(value) if value is not None else "")
    for index, image in enumerate(images, 1):
        picture = document.add_picture(str(image), width=Inches(6.0))
        max_height = Inches(8.0)
        if picture.height > max_height:
            scale = max_height / picture.height
            picture.height = max_height
            picture.width = int(picture.width * scale)
        document.add_paragraph(f"Figure {index}. {image.name}")
    if sources:
        document.add_heading("References and source links", level=1)
        for source in sources:
            document.add_paragraph(source, style="List Number")
    document.save(path)


def _excel_safe_title(value: str, used: set[str]) -> str:
    base = re.sub(r"[\[\]:*?/\\']", "_", value).strip("'")[:31] or "Data"
    name = base
    index = 2
    while name.casefold() in used:
        tail = f"_{index}"
        name = f"{base[:31 - len(tail)]}{tail}"
        index += 1
    used.add(name.casefold())
    return name


def _write_excel(path: Path, title: str, content: str, sections: list[dict],
                 tables: list[dict], sources: list[str], images: list[Path],
                 chart_type: str, source_path: str = "") -> None:
    from openpyxl import Workbook, load_workbook
    from openpyxl.chart import BarChart, LineChart, Reference
    from openpyxl.drawing.image import Image as SpreadsheetImage
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter

    workbook = (
        load_workbook(source_path)
        if source_path and Path(source_path).suffix.lower() == ".xlsx"
        else Workbook()
    )
    if not source_path:
        workbook.remove(workbook.active)
    used: set[str] = {name.casefold() for name in workbook.sheetnames}
    analysis_rows = [["Dataset", "Numeric field", "Count", "Average", "Minimum", "Maximum"]]

    for index, table in enumerate(tables, 1):
        name = _excel_safe_title(table["title"] or f"Data {index}", used)
        worksheet = workbook.create_sheet(name)
        worksheet.append([_safe_cell(header) for header in table["headers"]])
        for header_cell in worksheet[1]:
            header_cell.font = Font(bold=True, color="FFFFFF")
            header_cell.fill = PatternFill("solid", fgColor="123B5D")
            header_cell.alignment = Alignment(wrap_text=True, vertical="top")
        for row in table["rows"]:
            worksheet.append([_safe_cell(value) for value in row])
        worksheet.freeze_panes = "A2"
        worksheet.auto_filter.ref = worksheet.dimensions

        for column_index, header in enumerate(table["headers"], 1):
            letter = get_column_letter(column_index)
            values = [row[column_index - 1] for row in table["rows"]]
            numeric_values = [
                value for value in values
                if isinstance(_safe_cell(value), (int, float))
                and not isinstance(_safe_cell(value), bool)
            ]
            if numeric_values and worksheet.max_row > 1:
                data_range = f"'{name}'!{letter}2:{letter}{worksheet.max_row}"
                analysis_rows.append([
                    _safe_cell(name), _safe_cell(header),
                    f"=COUNT({data_range})",
                    f"=AVERAGE({data_range})",
                    f"=MIN({data_range})",
                    f"=MAX({data_range})",
                ])
            widths = [len(str(header))]
            widths.extend(len(str(row[column_index - 1] or "")) for row in table["rows"][:200])
            worksheet.column_dimensions[letter].width = min(max(max(widths) + 2, 12), 42)

        numeric_columns = []
        for column_index in range(2, len(table["headers"]) + 1):
            if any(
                isinstance(_safe_cell(row[column_index - 1]), (int, float))
                and not isinstance(_safe_cell(row[column_index - 1]), bool)
                for row in table["rows"]
            ):
                numeric_columns.append(column_index)
        if table["rows"] and numeric_columns:
            chart = LineChart() if chart_type == "line" else BarChart()
            chart.title = table["title"] or title
            chart.y_axis.title = "Value"
            chart.x_axis.title = table["headers"][0]
            chart.height = 8
            chart.width = 16
            data = Reference(
                worksheet, min_col=numeric_columns[0],
                max_col=numeric_columns[min(2, len(numeric_columns) - 1)],
                min_row=1, max_row=worksheet.max_row,
            )
            categories = Reference(
                worksheet, min_col=1, min_row=2, max_row=worksheet.max_row
            )
            chart.add_data(data, titles_from_data=True)
            chart.set_categories(categories)
            worksheet.add_chart(chart, f"{get_column_letter(len(table['headers']) + 2)}2")

    if len(analysis_rows) > 1:
        analysis = workbook.create_sheet(_excel_safe_title("Analysis", used))
        for row in analysis_rows:
            analysis.append(row)
        for cell in analysis[1]:
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill("solid", fgColor="123B5D")
        analysis.freeze_panes = "A2"
        analysis.auto_filter.ref = analysis.dimensions
        for column in analysis.columns:
            analysis.column_dimensions[get_column_letter(column[0].column)].width = 22

    notes = []
    if content:
        notes.append(content)
    notes.extend(
        f"{section['heading']}\n{section['body']}".strip()
        for section in sections
        if section["heading"] or section["body"]
    )
    if sources:
        notes.append("References and source links:\n" + "\n".join(sources))
    if notes or not tables:
        worksheet = workbook.create_sheet(_excel_safe_title("Notes", used))
        worksheet.append([_safe_cell(title)])
        worksheet["A1"].font = Font(bold=True, size=14)
        for note in notes:
            worksheet.append([_safe_cell(note)])
        worksheet.column_dimensions["A"].width = 110
        for row in worksheet.iter_rows():
            for cell in row:
                cell.alignment = Alignment(wrap_text=True, vertical="top")
    if images:
        figures = workbook.create_sheet(_excel_safe_title("Figures", used))
        figures.append(["User-provided figures"])
        figures["A1"].font = Font(bold=True, size=14)
        row = 3
        for image_path in images:
            figures.cell(row=row, column=1, value=_safe_cell(image_path.name))
            image = SpreadsheetImage(str(image_path))
            scale = min(1.0, 720 / image.width, 420 / image.height)
            image.width = int(image.width * scale)
            image.height = int(image.height * scale)
            figures.add_image(image, f"A{row + 1}")
            row += max(25, int(image.height / 20) + 2)
    workbook.save(path)


def _write_powerpoint(path: Path, title: str, content: str, sections: list[dict],
                      tables: list[dict], slides: list[dict], images: list[Path],
                      sources: list[str], chart_type: str,
                      source_path: str = "") -> None:
    from pptx import Presentation
    from pptx.chart.data import CategoryChartData
    from pptx.dml.color import RGBColor
    from pptx.enum.chart import XL_CHART_TYPE
    from pptx.util import Inches, Pt

    presentation = Presentation(source_path) if source_path else Presentation()
    presentation.core_properties.title = title
    if not source_path:
        presentation.slides.add_slide(
            presentation.slide_layouts[0]
        ).shapes.title.text = title

    prepared_slides = list(slides)
    if not prepared_slides:
        prepared_slides = [
            {"title": section["heading"] or f"Section {index}", "body": section["body"], "bullets": []}
            for index, section in enumerate(sections, 1)
        ]
    if not prepared_slides and content:
        prepared_slides = [
            {"title": title, "body": content[:8_000], "bullets": []}
        ]

    for item in prepared_slides:
        slide = presentation.slides.add_slide(presentation.slide_layouts[1])
        slide.shapes.title.text = item["title"] or title
        placeholder = slide.placeholders[1]
        text_frame = placeholder.text_frame
        text_frame.clear()
        lines = [line.strip() for line in item["body"].splitlines() if line.strip()]
        if lines:
            text_frame.paragraphs[0].text = lines[0]
            for line in lines[1:]:
                paragraph = text_frame.add_paragraph()
                paragraph.text = line
        for bullet in item["bullets"]:
            paragraph = text_frame.add_paragraph()
            paragraph.text = bullet
            paragraph.level = 0

    for table in tables:
        slide = presentation.slides.add_slide(presentation.slide_layouts[6])
        heading = slide.shapes.add_textbox(Inches(0.5), Inches(0.25), Inches(12), Inches(0.6))
        heading.text_frame.text = table["title"] or "Research table"
        heading.text_frame.paragraphs[0].font.size = Pt(24)
        visible_rows = table["rows"][:12]
        ppt_table = slide.shapes.add_table(
            len(visible_rows) + 1, len(table["headers"]),
            Inches(0.5), Inches(1.1), Inches(12.3), Inches(5.2),
        ).table
        for col_index, header in enumerate(table["headers"]):
            ppt_table.cell(0, col_index).text = header
            ppt_table.cell(0, col_index).fill.solid()
            ppt_table.cell(0, col_index).fill.fore_color.rgb = RGBColor(18, 59, 93)
            for paragraph in ppt_table.cell(0, col_index).text_frame.paragraphs:
                paragraph.font.bold = True
                paragraph.font.color.rgb = RGBColor(255, 255, 255)
                paragraph.font.size = Pt(12)
        for row_index, row in enumerate(visible_rows, 1):
            for col_index, value in enumerate(row):
                ppt_table.cell(row_index, col_index).text = str(_safe_cell(value) or "")
                for paragraph in ppt_table.cell(row_index, col_index).text_frame.paragraphs:
                    paragraph.font.size = Pt(10)
        if len(table["rows"]) > len(visible_rows):
            note = slide.shapes.add_textbox(Inches(0.5), Inches(6.45), Inches(12), Inches(0.35))
            note.text_frame.text = (
                f"Preview: first {len(visible_rows)} of {len(table['rows'])} rows."
            )
            note.text_frame.paragraphs[0].font.size = Pt(10)

    if tables:
        table = next(
            (item for item in tables if item["rows"] and len(item["headers"]) > 1),
            None,
        )
        if table:
            numeric_columns = []
            for column_index in range(1, len(table["headers"])):
                if any(
                    isinstance(_safe_cell(row[column_index]), (int, float))
                    and not isinstance(_safe_cell(row[column_index]), bool)
                    for row in table["rows"]
                ):
                    numeric_columns.append(column_index)
            if numeric_columns:
                data = CategoryChartData()
                data.categories = [str(row[0]) for row in table["rows"]]
                for column_index in numeric_columns[:3]:
                    values = []
                    for row in table["rows"]:
                        value = _safe_cell(row[column_index])
                        values.append(value if isinstance(value, (int, float)) else 0)
                    data.add_series(table["headers"][column_index], values)
                slide = presentation.slides.add_slide(presentation.slide_layouts[5])
                slide.shapes.title.text = f"{table['title'] or title} — chart"
                chart_kind = (
                    XL_CHART_TYPE.LINE
                    if chart_type == "line"
                    else XL_CHART_TYPE.COLUMN_CLUSTERED
                )
                slide.shapes.add_chart(
                    chart_kind, Inches(0.8), Inches(1.2), Inches(11.5),
                    Inches(5.5), data,
                )

    for image in images:
        slide = presentation.slides.add_slide(presentation.slide_layouts[6])
        picture = slide.shapes.add_picture(
            str(image), Inches(0.8), Inches(0.7), width=Inches(11.5)
        )
        max_height = Inches(5.8)
        if picture.height > max_height:
            scale = max_height / picture.height
            picture.height = max_height
            picture.width = int(picture.width * scale)
        picture.left = int((presentation.slide_width - picture.width) / 2)
        picture.top = Inches(0.7) + int((max_height - picture.height) / 2)

    if sources:
        slide = presentation.slides.add_slide(presentation.slide_layouts[1])
        slide.shapes.title.text = "References and source links"
        frame = slide.placeholders[1].text_frame
        frame.clear()
        for index, source in enumerate(sources):
            paragraph = frame.paragraphs[0] if index == 0 else frame.add_paragraph()
            paragraph.text = source
            paragraph.font.size = Pt(14)
    presentation.save(path)


def _open_with_default_app(path: Path) -> None:
    if os.name == "nt":
        os.startfile(str(path))
    elif sys.platform == "darwin":
        subprocess.Popen(["open", str(path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        subprocess.Popen(["xdg-open", str(path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def create_office_document(parameters: dict) -> str:
    params = parameters or {}
    requested_format = _text(params.get("format"), "format", 30).lower()
    suffix = _FORMAT_EXTENSIONS.get(requested_format)
    if not suffix:
        raise ValueError("format must be Word (.docx), Excel (.xlsx), or PowerPoint (.pptx).")

    title = _text(params.get("title"), "title", 300) or "JARVIS Research Document"
    content = _text(params.get("content"), "content")
    sections = _sections(params.get("sections"))
    tables = _tables(params.get("tables"))
    slides = _slides(params.get("slides"))
    images = _image_paths(params.get("image_paths"))
    sources = _sources(params.get("sources"))
    chart_type = _text(params.get("chart_type"), "chart_type", 20).lower()
    if chart_type not in {"bar", "line"}:
        chart_type = "bar"

    source_path = _text(params.get("source_path"), "source_path", 4_000)
    if source_path:
        source = Path(source_path).expanduser()
        if not source.is_file():
            raise ValueError(f"Source file not found: {source_path}")
        allowed_source = {
            ".docx": {".docx"},
            ".xlsx": {".xlsx", ".csv"},
            ".pptx": {".pptx"},
        }
        if source.suffix.lower() not in allowed_source[suffix]:
            raise ValueError(
                f"Source for {suffix} must be one of "
                f"{', '.join(sorted(allowed_source[suffix]))}."
            )
        if suffix == ".xlsx" and source.suffix.lower() == ".csv":
            tables = [_load_source_table(source_path)] + tables

    if suffix == ".docx" and not any((content, sections, tables, images, sources)):
        raise ValueError("Add document content, sections, a table, an image, or references.")
    if suffix == ".pptx" and not any((content, sections, slides, tables, images)):
        raise ValueError("Add slide content, a table, or an image.")
    if suffix == ".xlsx" and not any((content, sections, tables, sources)):
        raise ValueError("Add workbook data, notes, sections, or references.")

    output = _output_path(
        _text(params.get("output_path"), "output_path", 4_000),
        title,
        suffix,
        source_path,
    )
    if suffix == ".docx":
        writer = lambda path: _write_word(
            path, title, content, sections, tables, images, sources, source_path
        )
        label = "Word document"
    elif suffix == ".xlsx":
        writer = lambda path: _write_excel(
            path, title, content, sections, tables, sources, images, chart_type,
            source_path,
        )
        label = "Excel workbook"
    else:
        writer = lambda path: _write_powerpoint(
            path, title, content, sections, tables, slides, images, sources,
            chart_type, source_path,
        )
        label = "PowerPoint presentation"

    _save_new_file(output, writer)
    result = f"Created {label}: {output}"
    if params.get("open_after") is True:
        try:
            _open_with_default_app(output)
            result += "\nOpened with the system's default application."
        except OSError as exc:
            result += f"\nSaved successfully, but could not open the file: {exc}"
    return result


def office_studio(parameters: dict, **_context) -> str:
    return create_office_document(parameters)


TOOL = {
    "name": "office_studio",
    "description": (
        "Create editable Word (.docx), Excel (.xlsx), and PowerPoint (.pptx) files "
        "for research and study. Supports structured sections, tables, references, "
        "images, charts, and importing CSV/XLSX datasets into a new workbook. For "
        "revision requests, it can append new material to a copy of an existing "
        "Word/Excel/PowerPoint file while preserving the original. "
        "research, search or inspect the user's sources first; do not invent citations "
        "or claim unverified facts. This action creates a new file and never overwrites "
        "an existing file. Set open_after=true only when the user wants it opened in "
        "the system's Office application."
    ),
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "format": {
                "type": "STRING",
                "description": "word/docx, excel/xlsx, or powerpoint/pptx",
            },
            "title": {"type": "STRING", "description": "Document or workbook title"},
            "content": {
                "type": "STRING",
                "description": "Main text, notes, or explanation",
            },
            "sections": {
                "type": "ARRAY",
                "description": "Word sections or report notes: objects with heading and body",
                "items": {
                    "type": "OBJECT",
                    "properties": {
                        "heading": {"type": "STRING"},
                        "body": {"type": "STRING"},
                    },
                },
            },
            "tables": {
                "type": "ARRAY",
                "description": "Tables: each object has title, headers (strings), and rows (arrays of cell values)",
                "items": {
                    "type": "OBJECT",
                    "properties": {
                        "title": {"type": "STRING"},
                        "headers": {"type": "ARRAY", "items": {"type": "STRING"}},
                        "rows": {
                            "type": "ARRAY",
                            "items": {
                                "type": "ARRAY",
                                "items": {"type": "STRING"},
                            },
                        },
                    },
                },
            },
            "slides": {
                "type": "ARRAY",
                "description": "PowerPoint slides: title, body, and bullets",
                "items": {
                    "type": "OBJECT",
                    "properties": {
                        "title": {"type": "STRING"},
                        "body": {"type": "STRING"},
                        "bullets": {"type": "ARRAY", "items": {"type": "STRING"}},
                    },
                },
            },
            "sources": {
                "type": "ARRAY",
                "description": "Verified source citations, DOI links, or URLs",
                "items": {"type": "STRING"},
            },
            "image_paths": {
                "type": "ARRAY",
                "description": "User-provided local image paths to embed",
                "items": {"type": "STRING"},
            },
            "source_path": {
                "type": "STRING",
                "description": "Optional existing Office file to extend as a new copy, or CSV/XLSX dataset to import into Excel",
            },
            "chart_type": {
                "type": "STRING",
                "description": "Excel/PowerPoint chart style: bar or line",
            },
            "output_path": {
                "type": "STRING",
                "description": "Optional output file path; a unique name is used if it already exists",
            },
            "open_after": {
                "type": "BOOLEAN",
                "description": "Open the saved file in the system's default application only when requested",
            },
        },
    },
    "handler": office_studio,
}
