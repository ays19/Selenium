"""
DMS-TC093
Bulk Upload Template  Download
1. Go to https://ecmv6.robo2mation.com/dms/document/upload/bulk-upload/
2. Type & select a doc-type
3. Click on "Download" template
Selected doc-type bulk upload template should be downloaded
"""
import os

import common as c

TEST_CASE_ID = "DMS-TC093"


def template_download(session: c.DmsSession) -> tuple[bool, str]:
    doc_type = os.getenv("BULK_DOC_TYPE", "").strip()
    path = session.bulk_upload.download_template(doc_type)
    size = os.path.getsize(path)
    header = session.bulk_upload.template_header(path)
    doc_id = session.bulk_upload.selected_doc_type_id()
    meta_fields, _ = session.bulk_upload.fetch_metadata_and_unique_values(doc_id)

    expected_meta_cols = {title.upper() for title in meta_fields}
    actual_cols = [col.strip().upper() for col in header]
    has_required_cols = (
        len(actual_cols) >= 3
        and actual_cols[0] == "DOCUMENT_NAME"
        and "__FILE_NAME" in actual_cols
        and "STATUS" in actual_cols
        and expected_meta_cols.issubset(set(actual_cols))
    )
    ok = size > 0 and has_required_cols
    return ok, f"Template downloaded: {os.path.basename(path)} ({size} bytes), header={header}"


SCENARIOS = [("Template download", template_download)]


def main() -> None:
    c.run_dms_test(
        TEST_CASE_ID,
        SCENARIOS,
        doc=__doc__,
        required_env=[("BULK_DOC_TYPE", "(search text of a doc-type for bulk upload)")],
    )


if __name__ == "__main__":
    main()
