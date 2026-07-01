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

    def test_materialize_pose_labels_writes_sidecar_json_for_each_normalized_image(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = processor.prepare_output_dirs(root / "out")
            image_path = paths["normalized"] / "good" / "0001-student-a.jpg"
            image_path.write_bytes(b"image")
            source = processor.SourceImage(
                source_path="Student/good/a.jpg",
                participant="student",
                label="good",
                extracted_path=image_path,
                sha256="abc",
                normalized_path=image_path,
            )

            batch_zip = root / "batch_export.zip"
            with zipfile.ZipFile(batch_zip, "w") as zf:
                zf.writestr(
                    "pose_labels/standing/0001-student-a.json",
                    """
                    {
                      "format": "yolo-pose-json-v1",
                      "image": {"file_name": "0001-student-a.jpg"},
                      "metadata": {"source_name": "0001-student-a.jpg"},
                      "annotations": []
                    }
                    """,
                )

            count = processor.materialize_pose_label_jsons(batch_zip, [source], paths["pose_labels"])

            sidecar = image_path.with_suffix(".json")
            centralized = paths["pose_labels"] / "good" / "0001-student-a.json"
            self.assertEqual(1, count)
            self.assertTrue(sidecar.is_file())
            self.assertTrue(centralized.is_file())
            self.assertEqual(centralized, source.pose_label_path)
            self.assertIn('"inferred_label": "good"', sidecar.read_text())

    def test_materialize_pose_labels_prefers_export_index_for_duplicate_names(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = processor.prepare_output_dirs(root / "out")
            good_path = paths["normalized"] / "good" / "0001-sample.jpg"
            bad_path = paths["normalized"] / "bad" / "0001-sample.jpg"
            good_path.parent.mkdir(parents=True, exist_ok=True)
            bad_path.parent.mkdir(parents=True, exist_ok=True)
            good_path.write_bytes(b"good")
            bad_path.write_bytes(b"bad")
            good_source = processor.SourceImage(
                source_path="Student/good/sample.jpg",
                participant="student",
                label="good",
                extracted_path=good_path,
                sha256="good",
                normalized_path=good_path,
            )
            bad_source = processor.SourceImage(
                source_path="Student/bad/sample.jpg",
                participant="student",
                label="bad",
                extracted_path=bad_path,
                sha256="bad",
                normalized_path=bad_path,
            )

            batch_zip = root / "batch_export.zip"
            with zipfile.ZipFile(batch_zip, "w") as zf:
                zf.writestr(
                    "pose_labels/standing/0002-0001-sample.json",
                    """
                    {
                      "format": "yolo-pose-json-v1",
                      "image": {"file_name": "0001-sample.jpg"},
                      "metadata": {
                        "source_name": "0001-sample.jpg",
                        "original_file": "standing/0002-0001-sample.jpg"
                      },
                      "annotations": []
                    }
                    """,
                )

            count = processor.materialize_pose_label_jsons(
                batch_zip,
                [good_source, bad_source],
                paths["pose_labels"],
            )

            self.assertEqual(1, count)
            self.assertFalse(good_path.with_suffix(".json").exists())
            self.assertTrue(bad_path.with_suffix(".json").exists())
            self.assertEqual(paths["pose_labels"] / "bad" / "0001-sample.json", bad_source.pose_label_path)


if __name__ == "__main__":
    unittest.main()
