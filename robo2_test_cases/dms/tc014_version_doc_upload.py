"""
DMS-TC014
Version Doc Upload
"1. Open a document
2. Click on ""Add"" icon on version history
3. Select new version doc, can give file name extended part
4. Click on ""Save Changes
Version doc should be uploaded with proper confirmation message. Extended name should show.
"""
import common as c

TEST_CASE_ID = "DMS-TC014"
EXTENDED_NAME = "AUTO_v2"


def version_upload(session: c.DmsSession) -> tuple[bool, str]:
    session.new_document()
    sample = session.upload.find_sample_file("pdf")
    if not sample:
        raise c.SetupError(f"no .pdf sample file in {c.SAMPLE_DIR}")
    _, pdf_copy = session.upload.unique_copy(sample[1])

    ok, message = session.document.add_version(pdf_copy, EXTENDED_NAME)
    if not ok:
        return False, message

    shown = session.document.is_version_listed(EXTENDED_NAME)
    return shown, f"{message}. Extended name '{EXTENDED_NAME}' " + (
        "shown in version history" if shown else "not shown in version history"
    )


SCENARIOS = [("Version upload", version_upload)]


def main() -> None:
    c.run_dms_test(TEST_CASE_ID, SCENARIOS, doc=__doc__)


if __name__ == "__main__":
    main()
