"""
DMS-TC095
Bulk Upload Template Upload
1. Go to https://ecmv6.robo2mation.com/dms/document/upload/bulk-upload/
2. Type & select a doc-type
3. upload bulk upload template csv (correct data, few row data)
System should upload the documents with confirmation message
"""
from datetime import datetime
import os

import common as c

TEST_CASE_ID = "DMS-TC095"


def bulk_upload(session: c.DmsSession) -> tuple[bool, str]:
    doc_type = os.getenv("BULK_DOC_TYPE", "").strip()
    template = session.bulk_upload.download_template(doc_type)
    header = session.bulk_upload.template_header(template)
    doc_id = session.bulk_upload.selected_doc_type_id()
    meta_fields, unique_vals = session.bulk_upload.fetch_metadata_and_unique_values(doc_id)
    date_fmt = session.bulk_upload.system_date_format()

    run_id = datetime.now().strftime("%H%M%S")
    files = []
    for ext in ("pdf", "txt"):
        sample = session.upload.find_sample_file(ext)
        if not sample:
            raise c.SetupError(f"no .{ext} sample file in {c.SAMPLE_DIR}")
        files.append(session.upload.unique_copy(sample[1])[1])

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
        return False, f"{message}; uploaded docs missing from Quick Search: {missing}"
    return True, f"{message}; verified in Quick Search: {doc_names}"


SCENARIOS = [("Valid template", bulk_upload)]


def main() -> None:
    c.run_dms_test(
        TEST_CASE_ID,
        SCENARIOS,
        doc=__doc__,
        required_env=[("BULK_DOC_TYPE", "(search text of a doc-type for bulk upload)")],
    )


if __name__ == "__main__":
    main()
