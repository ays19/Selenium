"""
DMS-TC022
Download Document
1. Open a document
2. Click on "download"
Document should be downloaded
"""
import common as c

TEST_CASE_ID = "DMS-TC022"


def download_document(session: c.DmsSession) -> tuple[bool, str]:
    session.new_document()
    file_name = session.document.download_current()
    if file_name:
        return True, f"Document downloaded: {file_name}"
    return False, "no file was downloaded after clicking Download"


SCENARIOS = [("Download", download_document)]


def main() -> None:
    c.run_dms_test(TEST_CASE_ID, SCENARIOS, doc=__doc__)


if __name__ == "__main__":
    main()
