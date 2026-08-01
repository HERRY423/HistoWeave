"""Import the authorized CRC pathology CSVs into one canonical truth table."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd


def digest(path: Path, algorithm: str = "sha256") -> str:
    value = hashlib.new(algorithm)
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def import_truth(
    prepared: Path,
    annotation_dir: Path,
    annotation_archive: Path,
    authorization_path: Path,
    output: Path,
) -> dict[str, object]:
    authorization = json.loads(authorization_path.read_text(encoding="utf-8"))
    if authorization.get("truth_unseal_authorized") is not True:
        raise ValueError("joint truth-unseal authorization is required")
    source_path = prepared / "source_manifest.json"
    if digest(source_path) != authorization.get("source_manifest_sha256"):
        raise ValueError("prepared source manifest does not match authorization")
    source = json.loads(source_path.read_text(encoding="utf-8"))
    sample_ids = [str(row["sample_id"]) for row in source["records"]]
    rows: list[pd.DataFrame] = []
    records: list[dict[str, object]] = []
    for sample_id in sample_ids:
        path = annotation_dir / f"Pathologist_Annotations_{sample_id}.csv"
        if not path.is_file():
            raise FileNotFoundError(f"missing annotation CSV: {path}")
        frame = pd.read_csv(path, dtype=str)
        if len(frame.columns) != 2 or frame.columns[0].strip().lower() != "barcode":
            raise ValueError(f"unexpected annotation schema: {path.name}")
        canonical = frame.iloc[:, :2].copy()
        canonical.columns = ["spot_id", "truth_label"]
        canonical["spot_id"] = canonical["spot_id"].str.strip()
        canonical["truth_label"] = canonical["truth_label"].str.strip()
        missing = canonical.isna().any(axis=1) | (canonical == "").any(axis=1)
        excluded = canonical["truth_label"].str.casefold().eq("exclude")
        keep = ~(missing | excluded)
        retained = canonical.loc[keep].copy()
        if retained.empty or retained["spot_id"].duplicated().any():
            raise ValueError(f"empty or duplicate retained annotations: {path.name}")
        retained.insert(0, "sample_id", sample_id)
        rows.append(retained)
        records.append(
            {
                "sample_id": sample_id,
                "source_csv": path.name,
                "source_csv_sha256": digest(path),
                "rows_total": int(len(canonical)),
                "rows_retained": int(keep.sum()),
                "rows_excluded_label": int(excluded.sum()),
                "rows_missing": int(missing.sum()),
                "n_truth_categories": int(retained["truth_label"].nunique()),
            }
        )
    truth = pd.concat(rows, ignore_index=True)
    if truth.duplicated(["sample_id", "spot_id"]).any():
        raise ValueError("canonical truth contains duplicate sample/spot identifiers")
    output.parent.mkdir(parents=True, exist_ok=True)
    truth.to_csv(output, index=False)
    manifest = {
        "schema_version": "histoweave.crc.truth_import.v4",
        "imported_utc": datetime.now(UTC).isoformat(),
        "protocol_id": authorization["protocol_id"],
        "truth_unseal_authorization_sha256": digest(authorization_path),
        "annotation_archive_md5": digest(annotation_archive, "md5"),
        "annotation_archive_sha256": digest(annotation_archive),
        "filter": "retain unique non-empty annotations except case-insensitive label 'exclude'",
        "label_harmonization": "none",
        "n_samples": len(sample_ids),
        "n_truth_rows": int(len(truth)),
        "truth_table_sha256": digest(output),
        "records": records,
    }
    manifest_path = output.with_name("truth_import_manifest.json")
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prepared", type=Path, required=True)
    parser.add_argument("--annotation-dir", type=Path, required=True)
    parser.add_argument("--annotation-archive", type=Path, required=True)
    parser.add_argument("--authorization", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    manifest = import_truth(
        args.prepared,
        args.annotation_dir,
        args.annotation_archive,
        args.authorization,
        args.output,
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
