import unittest
from types import SimpleNamespace

from src.api.schemas.exporting import ExportFormat
from src.api.services.exporters import ExportContext, ExporterRegistry


class ExporterTests(unittest.TestCase):
    def test_markdown_export_includes_required_legal_artifact_metadata(self) -> None:
        document = SimpleNamespace(
            title="Case report", document_key="case-report", version=2,
            content="The liability clause is capped.", citations_data=["chunk-123"],
        )
        case = SimpleNamespace(title="Acme v. Vendor")
        artifact = ExporterRegistry().get(ExportFormat.MARKDOWN).export(
            ExportContext(document=document, case=case, include_citations=True)
        )
        output = artifact.content.decode("utf-8")
        self.assertEqual(artifact.filename, "case-report-v2.md")
        self.assertIn("# Case report", output)
        self.assertIn("Case: Acme v. Vendor", output)
        self.assertIn("Version: 2", output)
        self.assertIn("- chunk-123", output)

    def test_citations_can_be_omitted(self) -> None:
        document = SimpleNamespace(title="Note", document_key="note", version=1, content="Text", citations_data=["chunk-123"])
        artifact = ExporterRegistry().get(ExportFormat.MARKDOWN).export(
            ExportContext(document=document, case=SimpleNamespace(title="Case"), include_citations=False)
        )
        self.assertNotIn("Citations:", artifact.content.decode("utf-8"))


if __name__ == "__main__":
    unittest.main()
