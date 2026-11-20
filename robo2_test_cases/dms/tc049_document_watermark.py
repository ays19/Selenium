"""
DMS-TC049
Document Watermark
1. Go to https://ecmv6.robo2mation.com/dms/document/upload/standard_upload/filesave/pendingmetalist/
2. Select a document type
3. Attach a pdf doc
4. Click on "Watermark File" field
5. Select a single watermark doc
6. Click on "Attach"
Document should be watermarked with proper confirmation message
"""
from datetime import datetime

import common as c

TEST_CASE_ID = "DMS-TC049"


def watermark_document(session: c.DmsSession) -> tuple[bool, str]:
    session.upload.prepare_upload("pdf")
    text = datetime.now().strftime("AUTO_WM_%H%M%S")
    ok, message = session.upload.create_text_watermark(text)
    if not ok:
        raise c.SetupError(f"could not create watermark ({message})")

    selected = session.upload.attach_watermark_from_library(text)
    if not selected:
        return False, "watermark was not attached to the document (no watermark name shown)"

    session.upload.set_document_name(datetime.now().strftime("AUTO_%H%M%S"))
    ok, message = session.upload.click_save_upload()
    return ok, f"Watermark '{selected}' attached. Upload message: {' '.join(message.split())}"


SCENARIOS = [("Document watermark", watermark_document)]


def main() -> None:
    c.run_dms_test(TEST_CASE_ID, SCENARIOS, doc=__doc__)


if __name__ == "__main__":
    main()
