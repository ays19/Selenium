"""
DMS-TC095
Bulk Upload Template Upload
1. Go to https://ecmv6.robo2mation.com/dms/document/upload/bulk-upload/
2. Type & select a doc-type
3. upload bulk upload template csv (correct data, few row data)
System should upload the documents with confirmation message

The test makes its own doc-type (two text meta-data, no unique / dropdown rules), so it can run again and again.
"""
from datetime import datetime
import os

import common as c

TEST_CASE_ID = "DMS-TC095"


def new_bulk_doc_type(session: c.DmsSession) -> str:
    doc_type = session.categorization.new_doc_type()
    session.categorization.new_metadata(doc_type, "One")
    session.categorization.new_metadata(doc_type, "Two")
    ok_pub, msg_pub = session.categorization.publish_doc_type(doc_type)
    if not ok_pub:
        raise c.SetupError(f"could not publish doc-type ({msg_pub})")
    return doc_type


def bulk_upload(session: c.DmsSession) -> tuple[bool, str]:
    doc_type = new_bulk_doc_type(session)
    template = session.bulk_upload.download_template(doc_type)
    header = session.bulk_upload.template_header(template)
    run_id = datetime.now().strftime("%H%M%S")

    files = []
    for ext in ("pdf", "txt"):
        sample = session.upload.find_sample_file(ext)
        if not sample:
            raise c.SetupError(f"no .{ext} sample file in {c.SAMPLE_DIR}")
        files.append(session.upload.unique_copy(sample[1])[1])

    rows = [
        [
            os.path.basename(path) if "file" in column.lower() else f"AUTO_{run_id}_{number}_{i}"
            for i, column in enumerate(header)
        ]
        for number, path in enumerate(files)
    ]
    csv_path = session.bulk_upload.write_csv(os.path.join(c.DOWNLOAD_DIR, "AUTO_bulk.csv"), header, rows)
    ok, message = session.bulk_upload.bulk_submit(doc_type, csv_path, files)
    session.bulk_upload.wait_for_ajax_idle(timeout=6)
    report_error = "error" in session.bulk_upload.body_text()
    return ok and not report_error, f"{message}. " + (
        "Upload record shows an error" if report_error else "No error shown"
    )


SCENARIOS = [("Valid template", bulk_upload)]


def main() -> None:
    c.run_dms_test(TEST_CASE_ID, SCENARIOS, doc=__doc__)


if __name__ == "__main__":
    main()
