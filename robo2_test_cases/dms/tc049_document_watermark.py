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

    doc_name = datetime.now().strftime("AUTO_WM_%H%M%S")
    session.upload.set_document_name(doc_name)
    ok, message = session.upload.click_save_upload()
    if not ok:
        return False, message
    if not session.explorer.search_finds(doc_name, tries=5):
        return False, f"Watermarked document '{doc_name}' uploaded ('{message}') but not found in Quick Search"
    return True, f"Watermark '{selected}' attached; '{doc_name}' uploaded ({' '.join(message.split())}) and found in Quick Search"


SCENARIOS = [("Document watermark", watermark_document)]


def main() -> None:
    c.run_dms_test(TEST_CASE_ID, SCENARIOS, doc=__doc__)


if __name__ == "__main__":
    main()
