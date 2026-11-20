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
    return size > 0, f"Template downloaded: {os.path.basename(path)} ({size} bytes)"


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
