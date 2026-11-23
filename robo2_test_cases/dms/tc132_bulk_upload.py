"""
DMS-TC132
Bulk Upload
1. Go to https://ecmv6.robo2mation.com/dms/document/upload/bulk-upload/
2. Follow bulk upload steps and upload files (1MB-20MB)
3. Observe the file uploading and the upload record report
Document bulk upload should be done without any errors with the correct data
"""
from datetime import datetime
import os

import common as c

TEST_CASE_ID = "DMS-TC132"


def prepare_sized_file(session: c.DmsSession, ext: str, min_mb: float = 1.1) -> str:
    sample = session.upload.find_sample_file(ext)
    if not sample:
        raise c.SetupError(f"no .{ext} sample file in {c.SAMPLE_DIR}")
    _, path = session.upload.unique_copy(sample[1])
    return session.bulk_upload.ensure_min_size(path, min_mb=min_mb)


def bulk_upload(session: c.DmsSession) -> tuple[bool, str]:
    doc_type = os.getenv("BULK_DOC_TYPE", "").strip()
    template = session.bulk_upload.download_template(doc_type)
    header = session.bulk_upload.template_header(template)
    doc_id = session.bulk_upload.selected_doc_type_id()
    meta_fields, unique_vals = session.bulk_upload.fetch_metadata_and_unique_values(doc_id)
    date_fmt = session.bulk_upload.system_date_format()

    run_id = datetime.now().strftime("%H%M%S")
    files = [prepare_sized_file(session, ext, min_mb=1.1) for ext in ("pdf", "ppt", "txt")]
    used_unique = {k: set(str(v) for v in vals if v is not None) for k, vals in unique_vals.items()}
    rows = [
        session.bulk_upload.build_valid_csv_row(header, idx, path, run_id, meta_fields, used_unique, date_fmt)
        for idx, path in enumerate(files)
    ]
    doc_names = [row[0] for row in rows]

    csv_path = session.bulk_upload.write_csv(os.path.join(c.DOWNLOAD_DIR, "AUTO_bulk.csv"), header, rows)
    ok, message = session.bulk_upload.bulk_submit(doc_type, csv_path, files)
    if not ok:
        return False, message

    missing = [name for name in doc_names if not session.explorer.search_finds(name, tries=3)]
    if missing:
        return False, f"{message}; uploaded 1MB+ docs missing from Quick Search: {missing}"
    return True, f"{message}; verified in Quick Search: {doc_names}"


SCENARIOS = [("Bulk upload", bulk_upload)]


def main() -> None:
    c.run_dms_test(
        TEST_CASE_ID,
        SCENARIOS,
        doc=__doc__,
        required_env=[("BULK_DOC_TYPE", "(search text of a doc-type for bulk upload)")],
    )


if __name__ == "__main__":
    main()
