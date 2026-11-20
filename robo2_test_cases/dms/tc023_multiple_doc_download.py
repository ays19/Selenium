"""
DMS-TC023
Multiple Doc Download Together
1. Go to advanced search
2. Select a doc type
3. Click on search
4. Select one, multiple or all documents
5. Click on "Download" icon
1. An URL should be generated in "Requested Download"
2. All selected documents should be downloaded as zip file when click on "Download" button
"""
import common as c

TEST_CASE_ID = "DMS-TC023"


def multiple_download(session: c.DmsSession) -> tuple[bool, str]:
    session.upload_document("pdf")
    first = session.upload_document("txt")
    return session.explorer.download_multiple_from_advanced_search(first["doc_type"])


SCENARIOS = [("Multiple download", multiple_download)]


def main() -> None:
    c.run_dms_test(TEST_CASE_ID, SCENARIOS, doc=__doc__)


if __name__ == "__main__":
    main()
