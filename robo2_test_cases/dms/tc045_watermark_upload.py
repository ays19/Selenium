"""
DMS-TC045
Watermark (Upload)
1. Go to https://ecmv6.robo2mation.com/dms/document/upload/standard_upload/filesave/pendingmetalist/
2. Select a document type
3. Click on "Watermark File" field
4. Go to "Upload" tab
5. Attach watermark doc (image or pdf file)
6. Click on "upload"
Watermark should be uploaded with proper confirmation message.
"""
import common as c

TEST_CASE_ID = "DMS-TC045"


def upload_watermark(session: c.DmsSession) -> tuple[bool, str]:
    session.upload.prepare_upload("pdf")
    sample = session.upload.find_sample_file("png")
    if not sample:
        raise c.SetupError(f"no .png sample file in {c.SAMPLE_DIR}")
    copy_name, copy_path = session.upload.unique_copy(sample[1])
    ok, message = session.upload.upload_watermark_file(copy_path)
    if not ok:
        return False, message
    stem = copy_name.rsplit(".", 1)[0]
    if not session.upload.is_watermark_in_library(stem):
        return False, f"Uploaded watermark '{stem}' did not appear in library ({message})"
    return True, f"{message} ('{stem}' verified in watermark library)"


SCENARIOS = [("Upload watermark", upload_watermark)]


def main() -> None:
    c.run_dms_test(TEST_CASE_ID, SCENARIOS, doc=__doc__)


if __name__ == "__main__":
    main()
