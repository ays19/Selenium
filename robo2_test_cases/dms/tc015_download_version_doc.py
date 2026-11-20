"""
DMS-TC015
Download version doc
1. Open a document with version doc
2. Click on on version history
3. Click on "Download" icon
Version doc should be downloaded
"""
import common as c

TEST_CASE_ID = "DMS-TC015"
EXTENDED_NAME = "AUTO_v2"


def version_download(session: c.DmsSession) -> tuple[bool, str]:
    session.new_document()
    sample = session.upload.find_sample_file("pdf")
    if not sample:
        raise c.SetupError(f"no .pdf sample file in {c.SAMPLE_DIR}")
    _, pdf_copy = session.upload.unique_copy(sample[1])

    ok, message = session.document.add_version(pdf_copy, EXTENDED_NAME)
    if not ok:
        raise c.SetupError(f"version doc could not be added ({message})")

    file_name = session.document.download_version(EXTENDED_NAME)
    if file_name:
        return True, f"Version doc downloaded: {file_name}"
    return False, "no file was downloaded after clicking the Download icon of the version"


SCENARIOS = [("Version download", version_download)]


def main() -> None:
    c.run_dms_test(TEST_CASE_ID, SCENARIOS, doc=__doc__)


if __name__ == "__main__":
    main()
