import tempfile
import unittest
import zipfile
from pathlib import Path

from scripts import process_documents_export as processor


class ProcessDocumentsExportTests(unittest.TestCase):
    def test_infer_label_from_common_folder_names(self):
        self.assertEqual("good", processor.infer_label(("Yuqi Jiao", "good posture", "a.jpg")))
        self.assertEqual("bad", processor.infer_label(("Feng Shuo Zhang", "bad_forward_head", "b.jpg")))
        self.assertEqual("good", processor.infer_label(("Tianxu Liu", "good.zip"), inherited_label=""))
        self.assertEqual("", processor.infer_label(("Jiapeng Xuan", "posture", "c.png")))

    def test_extract_nested_zip_and_normalize_unique_images(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            nested_zip = root / "good.zip"
            with zipfile.ZipFile(nested_zip, "w") as zf:
                zf.writestr("nested-good.jpg", b"same-image")
                zf.writestr("duplicate-good.jpg", b"same-image")

            export_zip = root / "documents.zip"
            with zipfile.ZipFile(export_zip, "w") as zf:
                zf.writestr("Student/good posture/a.jpg", b"good-image")
                zf.writestr("Student/bad posture/b.jpg", b"bad-image")
                zf.write(nested_zip, "Nested/good.zip")
                zf.writestr("Unknown/posture/c.png", b"unknown-image")

            output = root / "out"
            paths = processor.prepare_output_dirs(output)
            extracted = processor.extract_zip_images(export_zip, paths["extracted"])
            normalized = processor.normalize_images(extracted, paths["normalized"])

            copied = [item for item in normalized if item.normalized_path]
            duplicates = [item for item in normalized if item.duplicate_of]

            self.assertEqual(5, len(extracted))
            self.assertEqual(4, len(copied))
            self.assertEqual(1, len(duplicates))
            self.assertEqual(2, len([item for item in copied if item.label == "good"]))
            self.assertEqual(1, len([item for item in copied if item.label == "bad"]))
            self.assertEqual(1, len([item for item in copied if item.label == "unlabeled"]))


if __name__ == "__main__":
    unittest.main()
