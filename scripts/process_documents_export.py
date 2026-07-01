"""Process the team dataset export through the local web backend.

This script prepares a mixed cloud-export ZIP for the teacher's side-view
posture dataset task. It does not modify the original ZIP. It:

1. safely extracts images, including nested ``good.zip`` / ``bad.zip`` files;
2. normalizes known ``good`` / ``bad`` images into local working folders;
3. writes a source manifest with duplicates and label inference notes;
4. calls the existing Flask backend review and batch endpoints;
5. downloads the backend-generated ZIP reports;
6. materializes one YOLO-pose JSON sidecar for each processed image.

Usage
-----
    .venv/bin/python scripts/process_documents_export.py \
        --zip documents-export-2026-07-01.zip \
        --start-server

Outputs go under ``temp/`` by default and are ignored by Git.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import mimetypes
import os
import re
import shutil
import subprocess
import sys
import time
import uuid
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from urllib import error, request


PROJECT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_ZIP = PROJECT_DIR / "documents-export-2026-07-01.zip"
DEFAULT_OUTPUT = PROJECT_DIR / "temp" / "documents-export-2026-07-01-processed"
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
ZIP_EXTS = {".zip"}
KNOWN_LABELS = {"good", "bad"}
APP_VERSION = "week-02-yolo-pose-labels-v1"


@dataclass
class SourceImage:
    source_path: str
    participant: str
    label: str
    extracted_path: Path
    sha256: str
    duplicate_of: str = ""
    normalized_path: Path | None = None
    pose_label_path: Path | None = None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Normalize and process a team documents-export ZIP through the SURF web backend.",
    )
    parser.add_argument("--zip", default=str(DEFAULT_ZIP), help="Input documents-export ZIP.")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Output directory under temp/.")
    parser.add_argument("--base-url", default="http://127.0.0.1:5050", help="Running backend URL.")
    parser.add_argument("--start-server", action="store_true", help="Start the Flask backend if /health is unavailable.")
    parser.add_argument("--server-port", type=int, default=5050, help="Port to use when --start-server is set.")
    parser.add_argument("--timeout", type=int, default=1800, help="HTTP timeout in seconds for long dataset processing.")
    parser.add_argument("--dry-run", action="store_true", help="Only extract, normalize, and write manifests.")
    parser.add_argument("--max-files", type=int, default=0, help="Optional cap for debugging; 0 means no cap.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    zip_path = Path(args.zip).expanduser().resolve()
    if not zip_path.is_file():
        raise SystemExit(f"Input ZIP not found: {zip_path}")

    output_dir = unique_output_dir(Path(args.output).expanduser().resolve())
    paths = prepare_output_dirs(output_dir)

    print(f"Input ZIP: {zip_path}")
    print(f"Output: {output_dir}")

    raw_images = extract_zip_images(zip_path, paths["extracted"])
    if args.max_files > 0:
        raw_images = raw_images[: args.max_files]

    normalized_images = normalize_images(raw_images, paths["normalized"])
    write_manifest(normalized_images, paths["manifest"])

    known_good = [item.normalized_path for item in normalized_images if item.label == "good" and item.normalized_path]
    known_bad = [item.normalized_path for item in normalized_images if item.label == "bad" and item.normalized_path]
    unlabeled = [item.normalized_path for item in normalized_images if item.label == "unlabeled" and item.normalized_path]
    all_unique = [item.normalized_path for item in normalized_images if item.normalized_path]

    print(f"Source images: {len(raw_images)}")
    print(f"Unique images: {len(all_unique)}")
    print(f"Known good: {len(known_good)}")
    print(f"Known bad: {len(known_bad)}")
    print(f"Unlabeled: {len(unlabeled)}")

    backend_results: dict[str, dict] = {}
    pose_label_count = 0
    server_process: subprocess.Popen | None = None
    base_url = args.base_url.rstrip("/")

    try:
        if not args.dry_run:
            if not backend_ready(base_url):
                if not args.start_server:
                    raise SystemExit(
                        f"Backend not reachable at {base_url}. Start the demo first or rerun with --start-server."
                    )
                server_process, base_url = start_backend(paths["logs"], args.server_port)
            health = get_json(f"{base_url}/health", timeout=10)
            if health.get("version") != APP_VERSION:
                print(f"Warning: backend version is {health.get('version')}, expected {APP_VERSION}.")

            if known_good or known_bad:
                print("Calling /api/review-dataset for labeled good/bad images...")
                review_payload = post_multipart(
                    f"{base_url}/api/review-dataset",
                    files=[
                        *[("good_files", path) for path in known_good],
                        *[("bad_files", path) for path in known_bad],
                    ],
                    timeout=args.timeout,
                )
                backend_results["review"] = review_payload
                download_backend_zip(base_url, review_payload["download_url"], paths["exports"] / "review_export.zip", args.timeout)

            if all_unique:
                print("Calling /api/batch-analyze for standing/sitting/incomplete triage...")
                batch_payload = post_multipart(
                    f"{base_url}/api/batch-analyze",
                    files=[("files", path) for path in all_unique],
                    timeout=args.timeout,
                )
                backend_results["batch"] = batch_payload
                batch_zip_path = paths["exports"] / "batch_export.zip"
                download_backend_zip(base_url, batch_payload["download_url"], batch_zip_path, args.timeout)
                pose_label_count = materialize_pose_label_jsons(
                    batch_zip_path,
                    normalized_images,
                    paths["pose_labels"],
                )
                write_manifest(normalized_images, paths["manifest"])

    finally:
        if server_process is not None:
            server_process.terminate()
            try:
                server_process.wait(timeout=8)
            except subprocess.TimeoutExpired:
                server_process.kill()
                server_process.wait(timeout=5)

    write_json(paths["backend"] / "backend_responses.json", backend_results)
    write_summary(
        paths["summary"],
        zip_path=zip_path,
        output_dir=output_dir,
        raw_count=len(raw_images),
        unique_count=len(all_unique),
        good_count=len(known_good),
        bad_count=len(known_bad),
        unlabeled_count=len(unlabeled),
        pose_label_count=pose_label_count,
        backend_results=backend_results,
        dry_run=args.dry_run,
    )

    print(f"Manifest: {paths['manifest']}")
    print(f"Summary: {paths['summary']}")
    if not args.dry_run:
        print(f"Exports: {paths['exports']}")
    return 0


def unique_output_dir(path: Path) -> Path:
    if not path.exists():
        return path
    for index in range(2, 100):
        candidate = path.with_name(f"{path.name}-{index}")
        if not candidate.exists():
            return candidate
    raise RuntimeError(f"Could not choose a unique output directory for {path}")


def prepare_output_dirs(output_dir: Path) -> dict[str, Path]:
    paths = {
        "root": output_dir,
        "extracted": output_dir / "extracted",
        "normalized": output_dir / "normalized",
        "manifest": output_dir / "manifests" / "source_manifest.csv",
        "backend": output_dir / "backend",
        "exports": output_dir / "exports",
        "pose_labels": output_dir / "pose_labels",
        "logs": output_dir / "logs",
        "summary": output_dir / "summary.md",
    }
    for key, path in paths.items():
        if key in {"manifest", "summary"}:
            path.parent.mkdir(parents=True, exist_ok=True)
        else:
            path.mkdir(parents=True, exist_ok=True)
    for label in ("good", "bad", "unlabeled"):
        (paths["normalized"] / label).mkdir(parents=True, exist_ok=True)
    return paths


def extract_zip_images(zip_path: Path, output_dir: Path) -> list[SourceImage]:
    images: list[SourceImage] = []
    _extract_zip_images(zip_path, output_dir, images, inherited_label="")
    return images


def _extract_zip_images(
    zip_path: Path,
    output_dir: Path,
    images: list[SourceImage],
    inherited_label: str,
    prefix_parts: tuple[str, ...] = (),
) -> None:
    with zipfile.ZipFile(zip_path) as zf:
        for info in zf.infolist():
            if info.is_dir():
                continue
            original_parts = tuple(part for part in Path(info.filename).parts if part not in {"", ".", "__MACOSX"})
            if not original_parts:
                continue
            name = original_parts[-1]
            if name == ".DS_Store" or name.startswith("._"):
                continue

            ext = Path(name).suffix.lower()
            label = infer_label((*prefix_parts, *original_parts), inherited_label=inherited_label)
            participant = safe_part(original_parts[0]) if original_parts else "unknown"
            source_path = "/".join((*prefix_parts, *original_parts))
            data = zf.read(info)

            if ext in ZIP_EXTS:
                nested_zip = output_dir / "nested-zips" / f"{uuid.uuid4().hex}-{safe_part(name)}"
                nested_zip.parent.mkdir(parents=True, exist_ok=True)
                nested_zip.write_bytes(data)
                nested_label = infer_label((name,), inherited_label=label)
                _extract_zip_images(
                    nested_zip,
                    output_dir,
                    images,
                    inherited_label=nested_label,
                    prefix_parts=(*prefix_parts, *original_parts),
                )
                continue

            if ext not in IMAGE_EXTS:
                continue

            target_name = f"{len(images) + 1:04d}-{participant}-{safe_part(Path(name).stem)}{ext}"
            target_path = output_dir / "images" / target_name
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_bytes(data)
            images.append(
                SourceImage(
                    source_path=source_path,
                    participant=participant,
                    label=label or "unlabeled",
                    extracted_path=target_path,
                    sha256=sha256_bytes(data),
                )
            )


def infer_label(parts: Iterable[str], inherited_label: str = "") -> str:
    if inherited_label in KNOWN_LABELS:
        return inherited_label
    normalized_parts = [normalize_label_text(part) for part in parts]
    for part in normalized_parts:
        if re.search(r"(^|[^a-z])bad([^a-z]|$)", part) or "bad posture" in part or "bad forward head" in part:
            return "bad"
    for part in normalized_parts:
        if re.search(r"(^|[^a-z])good([^a-z]|$)", part) or "good posture" in part:
            return "good"
    return ""


def normalize_images(images: list[SourceImage], output_dir: Path) -> list[SourceImage]:
    seen: dict[str, SourceImage] = {}
    label_counts = {"good": 0, "bad": 0, "unlabeled": 0}
    for item in images:
        duplicate = seen.get(item.sha256)
        if duplicate is not None:
            item.duplicate_of = duplicate.source_path
            continue

        seen[item.sha256] = item
        label = item.label if item.label in {"good", "bad"} else "unlabeled"
        label_counts[label] += 1
        suffix = item.extracted_path.suffix.lower()
        target_name = f"{label_counts[label]:04d}-{item.participant}-{safe_part(item.extracted_path.stem)}{suffix}"
        target_path = output_dir / label / target_name
        shutil.copy2(item.extracted_path, target_path)
        item.normalized_path = target_path
    return images


def write_manifest(images: list[SourceImage], csv_path: Path) -> None:
    fieldnames = [
        "source_path",
        "participant",
        "inferred_label",
        "sha256",
        "duplicate_of",
        "extracted_path",
        "normalized_path",
        "pose_label_path",
    ]
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for item in images:
            writer.writerow(
                {
                    "source_path": item.source_path,
                    "participant": item.participant,
                    "inferred_label": item.label,
                    "sha256": item.sha256,
                    "duplicate_of": item.duplicate_of,
                    "extracted_path": str(item.extracted_path),
                    "normalized_path": "" if item.normalized_path is None else str(item.normalized_path),
                    "pose_label_path": "" if item.pose_label_path is None else str(item.pose_label_path),
                }
            )


def materialize_pose_label_jsons(batch_zip_path: Path, images: list[SourceImage], output_dir: Path) -> int:
    """Copy backend YOLO-pose JSON labels next to every normalized image.

    The backend batch ZIP stores labels under ``pose_labels/<category>/``. This
    script additionally writes:
    - ``pose_labels/<inferred-label>/<image-stem>.json`` for a clean label tree;
    - ``normalized/<inferred-label>/<image-stem>.json`` as a sidecar file.
    """
    if not batch_zip_path.is_file():
        return 0

    unique_images = [item for item in images if item.normalized_path is not None]
    by_index = {index: item for index, item in enumerate(unique_images, start=1)}
    by_name: dict[str, list[SourceImage]] = {}
    for item in unique_images:
        if item.normalized_path is None:
            continue
        by_name.setdefault(item.normalized_path.name, []).append(item)

    count = 0
    with zipfile.ZipFile(batch_zip_path) as zf:
        for member in sorted(zf.namelist()):
            if not member.startswith("pose_labels/") or not member.endswith(".json"):
                continue
            try:
                payload = json.loads(zf.read(member).decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                continue

            item = _source_image_for_pose_label(payload, by_index, by_name)
            if item is None:
                continue
            if item.normalized_path is None:
                continue

            label = item.label if item.label in {"good", "bad"} else "unlabeled"
            label_path = output_dir / label / f"{item.normalized_path.stem}.json"
            sidecar_path = item.normalized_path.with_suffix(".json")
            payload = _with_local_pose_label_metadata(
                payload,
                normalized_image=str(item.normalized_path),
                sidecar_label=str(sidecar_path),
                inferred_label=label,
                source_path=item.source_path,
            )
            write_json(label_path, payload)
            write_json(sidecar_path, payload)
            item.pose_label_path = label_path
            count += 1
    return count


def _pose_label_source_name(payload: dict) -> str:
    metadata = payload.get("metadata", {}) if isinstance(payload, dict) else {}
    image = payload.get("image", {}) if isinstance(payload, dict) else {}
    return str(metadata.get("source_name") or image.get("file_name") or "")


def _source_image_for_pose_label(
    payload: dict,
    by_index: dict[int, SourceImage],
    by_name: dict[str, list[SourceImage]],
) -> SourceImage | None:
    metadata = payload.get("metadata", {}) if isinstance(payload, dict) else {}
    original_file = str(metadata.get("original_file", ""))
    match = re.match(r"^\d{4}-", Path(original_file).name)
    if match:
        source = by_index.get(int(match.group(0)[:4]))
        if source is not None:
            return source

    source_name = _pose_label_source_name(payload)
    candidates = by_name.get(Path(source_name).name, [])
    if candidates:
        return candidates.pop(0)
    return None


def _with_local_pose_label_metadata(payload: dict, **metadata) -> dict:
    result = dict(payload)
    merged = dict(result.get("metadata", {}))
    merged.update({key: value for key, value in metadata.items() if value != ""})
    result["metadata"] = merged
    return result


def backend_ready(base_url: str) -> bool:
    try:
        payload = get_json(f"{base_url.rstrip('/')}/health", timeout=3)
    except Exception:
        return False
    return payload.get("app") == "surf-posture-web"


def start_backend(log_dir: Path, port: int) -> tuple[subprocess.Popen, str]:
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = open(log_dir / "backend.log", "w", encoding="utf-8")
    env = os.environ.copy()
    env["SURF_WEB_PORT"] = str(port)
    env["SURF_WEB_HOST"] = "127.0.0.1"
    process = subprocess.Popen(
        [sys.executable, "-m", "web.app"],
        cwd=PROJECT_DIR,
        env=env,
        stdout=log_file,
        stderr=subprocess.STDOUT,
    )
    base_url = f"http://127.0.0.1:{port}"
    for _ in range(60):
        if process.poll() is not None:
            raise RuntimeError(f"Backend exited early. See {log_dir / 'backend.log'}")
        if backend_ready(base_url):
            return process, base_url
        time.sleep(0.5)
    process.terminate()
    raise RuntimeError(f"Backend did not become ready. See {log_dir / 'backend.log'}")


def get_json(url: str, timeout: int) -> dict:
    with request.urlopen(url, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def post_multipart(url: str, files: list[tuple[str, Path]], timeout: int) -> dict:
    if not files:
        raise ValueError("post_multipart requires at least one file")
    boundary = f"----surf-{uuid.uuid4().hex}"
    body = bytearray()
    for field_name, path in files:
        body.extend(f"--{boundary}\r\n".encode("utf-8"))
        body.extend(
            (
                f'Content-Disposition: form-data; name="{field_name}"; '
                f'filename="{path.name}"\r\n'
            ).encode("utf-8")
        )
        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        body.extend(f"Content-Type: {content_type}\r\n\r\n".encode("utf-8"))
        body.extend(path.read_bytes())
        body.extend(b"\r\n")
    body.extend(f"--{boundary}--\r\n".encode("utf-8"))

    req = request.Request(
        url,
        data=bytes(body),
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Backend request failed with HTTP {exc.code}: {detail}") from exc


def download_backend_zip(base_url: str, download_url: str, target_path: Path, timeout: int) -> None:
    target_path.parent.mkdir(parents=True, exist_ok=True)
    url = f"{base_url.rstrip('/')}{download_url}"
    with request.urlopen(url, timeout=timeout) as response:
        target_path.write_bytes(response.read())


def write_summary(
    path: Path,
    *,
    zip_path: Path,
    output_dir: Path,
    raw_count: int,
    unique_count: int,
    good_count: int,
    bad_count: int,
    unlabeled_count: int,
    pose_label_count: int,
    backend_results: dict[str, dict],
    dry_run: bool,
) -> None:
    lines = [
        "# Documents Export Processing Summary",
        "",
        f"- Source ZIP: `{zip_path}`",
        f"- Output directory: `{output_dir}`",
        f"- Raw image entries: {raw_count}",
        f"- Unique images copied for backend processing: {unique_count}",
        f"- Known good images: {good_count}",
        f"- Known bad images: {bad_count}",
        f"- Unlabeled images: {unlabeled_count}",
        f"- YOLO-pose JSON labels materialized: {pose_label_count}",
        f"- Dry run: {dry_run}",
        "",
        "## Outputs",
        "",
        "- `manifests/source_manifest.csv`: source path, inferred label, duplicates, normalized path.",
        "- `normalized/good`, `normalized/bad`, `normalized/unlabeled`: local working copies.",
        "- `normalized/<label>/*.json`: YOLO-pose sidecar labels for each processed image when backend processing ran.",
        "- `pose_labels/<label>`: centralized YOLO-pose JSON label copies.",
        "- `exports/review_export.zip`: labeled good/bad review output when backend processing ran.",
        "- `exports/batch_export.zip`: all-image standing/sitting/incomplete triage output when backend processing ran.",
        "- `backend/backend_responses.json`: backend JSON summaries.",
        "",
    ]
    if "review" in backend_results:
        summary = backend_results["review"].get("summary", {})
        lines.extend(
            [
                "## Review Metrics",
                "",
                f"- Total: {summary.get('total')}",
                f"- Evaluated: {summary.get('evaluated')}",
                f"- Needs manual review: {summary.get('needs_review')}",
                f"- Accuracy: {summary.get('accuracy')}",
                f"- Precision: {summary.get('precision')}",
                f"- Recall: {summary.get('recall')}",
                f"- F1: {summary.get('f1')}",
                "",
            ]
        )
    if "batch" in backend_results:
        summary = backend_results["batch"].get("summary", {})
        counts = summary.get("counts", {})
        lines.extend(
            [
                "## Batch Triage",
                "",
                f"- Total: {summary.get('total')}",
                f"- Standing: {counts.get('standing')}",
                f"- Sitting: {counts.get('sitting')}",
                f"- Incomplete: {counts.get('incomplete')}",
                "",
            ]
        )
    path.write_text("\n".join(lines), encoding="utf-8")


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def normalize_label_text(value: str) -> str:
    value = value.lower().replace("_", " ").replace("-", " ")
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def safe_part(value: str) -> str:
    value = normalize_label_text(Path(value).name)
    value = re.sub(r"[^a-z0-9.]+", "-", value)
    value = value.strip("-")
    return value[:80] or "item"


if __name__ == "__main__":
    raise SystemExit(main())
