"""
DMS-TC016
Delete version doc
1. Open a document with one or more version doc
2. Click on on version history
3. Click on "Delete" icon of version doc
Version doc should be deleted with proper confirmation message
"""
import common as c

TEST_CASE_ID = "DMS-TC016"
EXTENDED_NAME = "AUTO_v2"


def version_delete(session: c.DmsSession) -> tuple[bool, str]:
    session.new_document()
    sample = session.upload.find_sample_file("pdf")
    if not sample:
        raise c.SetupError(f"no .pdf sample file in {c.SAMPLE_DIR}")
    _, pdf_copy = session.upload.unique_copy(sample[1])

    ok, message = session.document.add_version(pdf_copy, EXTENDED_NAME)
    if not ok:
        raise c.SetupError(f"version doc could not be added ({message})")

    return session.document.delete_version(EXTENDED_NAME)


SCENARIOS = [("Version delete", version_delete)]


def main() -> None:
    c.run_dms_test(TEST_CASE_ID, SCENARIOS, doc=__doc__)


if __name__ == "__main__":
    main()
