import csv
import tempfile
import unittest
from pathlib import Path

from docx import Document
from openpyxl import load_workbook
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE
from PIL import Image

from actions import office_studio


class OfficeStudioTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_word_export_includes_sections_tables_and_sources(self):
        output = self.root / "proposal.docx"
        result = office_studio.create_office_document({
            "format": "word",
            "title": "Research proposal",
            "sections": [{"heading": "Research question", "body": "How does X affect Y?"}],
            "tables": [{
                "title": "Study comparison",
                "headers": ["Study", "Method"],
                "rows": [["Example et al.", "Cohort"]],
            }],
            "sources": ["https://doi.org/10.0000/example"],
            "output_path": str(output),
        })

        self.assertIn(str(output), result)
        document = Document(output)
        paragraphs = [paragraph.text for paragraph in document.paragraphs]
        self.assertIn("Research question", paragraphs)
        self.assertIn("https://doi.org/10.0000/example", paragraphs)
        self.assertEqual(document.tables[0].cell(1, 0).text, "Example et al.")

    def test_excel_import_creates_analysis_chart_and_neutralizes_formula_text(self):
        source = self.root / "survey.csv"
        with source.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.writer(stream)
            writer.writerows([
                ['=HYPERLINK("https://example.org")', "score"],
                ["P01", "2"],
                ["P02", "4"],
                ["P03", "=1+1"],
            ])
        output = self.root / "survey_analysis.xlsx"
        office_studio.create_office_document({
            "format": "excel",
            "title": "Survey analysis",
            "content": '=HYPERLINK("https://example.org")',
            "source_path": str(source),
            "output_path": str(output),
        })

        workbook = load_workbook(output, data_only=False)
        data = workbook["survey"]
        self.assertEqual(data["A1"].value, '\' =HYPERLINK("https://example.org")'.replace("' ", "'"))
        self.assertEqual(data["A1"].data_type, "s")
        self.assertEqual(data["B2"].value, 2)
        self.assertEqual(data["B4"].value, "'=1+1")
        self.assertEqual(data["B4"].data_type, "s")
        self.assertTrue(data._charts)
        self.assertIn("Analysis", workbook.sheetnames)
        self.assertEqual(workbook["Analysis"]["D2"].value, "=AVERAGE('survey'!B2:B4)")
        self.assertEqual(workbook["Notes"]["A2"].value, '\' =HYPERLINK("https://example.org")'.replace("' ", "'"))
        self.assertEqual(workbook["Notes"]["A2"].data_type, "s")
        workbook.close()

    def test_powerpoint_export_includes_slide_table_and_chart(self):
        output = self.root / "defense.pptx"
        office_studio.create_office_document({
            "format": "powerpoint",
            "title": "Defense",
            "slides": [{
                "title": "Key finding",
                "body": "A concise summary",
                "bullets": ["Evidence-based", "Limitations stated"],
            }],
            "tables": [{
                "title": "Outcome data",
                "headers": ["Group", "Score"],
                "rows": [["Control", 4], ["Intervention", 7]],
            }],
            "sources": ["https://example.org/study"],
            "output_path": str(output),
        })

        presentation = Presentation(output)
        self.assertGreaterEqual(len(presentation.slides), 4)
        slide_text = [
            shape.text
            for slide in presentation.slides
            for shape in slide.shapes
            if hasattr(shape, "text")
        ]
        self.assertIn("Key finding", slide_text)
        self.assertTrue(any("Evidence-based" in text for text in slide_text))
        self.assertTrue(any(shape.has_table for slide in presentation.slides for shape in slide.shapes))
        self.assertTrue(any(shape.has_chart for slide in presentation.slides for shape in slide.shapes))

    def test_user_figure_is_embedded_in_all_three_office_formats(self):
        image_path = self.root / "figure.png"
        Image.new("RGB", (32, 24), color=(20, 120, 180)).save(image_path)
        paths = {
            "docx": self.root / "figure.docx",
            "xlsx": self.root / "figure.xlsx",
            "pptx": self.root / "figure.pptx",
        }
        for office_format, output in paths.items():
            office_studio.create_office_document({
                "format": office_format,
                "title": "Figure export",
                "content": "Figure notes",
                "image_paths": [str(image_path)],
                "output_path": str(output),
            })

        self.assertEqual(len(Document(paths["docx"]).inline_shapes), 1)
        workbook = load_workbook(paths["xlsx"])
        self.assertEqual(len(workbook["Figures"]._images), 1)
        workbook.close()
        presentation = Presentation(paths["pptx"])
        self.assertTrue(any(
            shape.shape_type == MSO_SHAPE_TYPE.PICTURE
            for slide in presentation.slides
            for shape in slide.shapes
        ))

    def test_revising_word_creates_a_copy_and_preserves_original(self):
        source = self.root / "original.docx"
        original = Document()
        original.add_paragraph("Original material")
        original.save(source)

        result = office_studio.create_office_document({
            "format": "docx",
            "title": "Revised section",
            "content": "New reviewed material",
            "source_path": str(source),
        })
        revised_path = Path(result.partition(": ")[2].splitlines()[0])

        self.assertTrue(source.is_file())
        self.assertNotEqual(source, revised_path)
        original_text = [paragraph.text for paragraph in Document(source).paragraphs]
        revised_text = [paragraph.text for paragraph in Document(revised_path).paragraphs]
        self.assertIn("Original material", original_text)
        self.assertIn("Original material", revised_text)
        self.assertIn("New reviewed material", revised_text)

    def test_existing_output_is_never_overwritten(self):
        output = self.root / "report.docx"
        output.write_bytes(b"keep this file")
        result = office_studio.create_office_document({
            "format": "docx",
            "title": "New report",
            "content": "Generated content",
            "output_path": str(output),
        })

        self.assertEqual(output.read_bytes(), b"keep this file")
        self.assertTrue((self.root / "report_2.docx").is_file())
        self.assertIn("report_2.docx", result)

    def test_invalid_format_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "format must be"):
            office_studio.create_office_document({
                "format": "pdf",
                "title": "Unsupported",
                "content": "Some content",
            })


if __name__ == "__main__":
    unittest.main()
