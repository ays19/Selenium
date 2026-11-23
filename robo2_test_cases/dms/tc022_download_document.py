"""
DMS-TC022
Download Document
1. Open a document
2. Click on "download"
Document should be downloaded
"""
import os

import common as c

TEST_CASE_ID = "DMS-TC022"


def download_document(session: c.DmsSession) -> tuple[bool, str]:
    session.new_document()
    file_name = session.document.download_current()
    if not file_name:
        return False, "no file was downloaded after clicking Download"
    full_path = os.path.join(c.DOWNLOAD_DIR, file_name)
    size = os.path.getsize(full_path) if os.path.isfile(full_path) else 0
    if size <= 0 or not file_name.lower().endswith(".pdf"):
        return False, f"unexpected downloaded file '{file_name}' ({size} bytes)"
    return True, f"Document downloaded: {file_name} ({size} bytes)"


SCENARIOS = [("Download", download_document)]


def main() -> None:
    c.run_dms_test(TEST_CASE_ID, SCENARIOS, doc=__doc__)


if __name__ == "__main__":
    main()
