"""
DMS-TC037
Document OCR
1. Go to https://ecmv6.robo2mation.com/dms/document/upload/standard_upload/
2. Try to attach a doc apart from pdf or image (jpg,jpeg or png)
3. Try to click on "OCR Document" icon
Document ocr should be done.
"""
import common as c

TEST_CASE_ID = "DMS-TC037"


def ocr(ext: str):
    def _scenario(session: c.DmsSession) -> tuple[bool, str]:
        info = session.upload_document(ext)
        name = info["name"]
        session.explorer.open_document(name)
        session.document.wait_for_page_load()
        session.document.expand_system_metadata()

        ocr_status = session.document.read_ocr_status()
        if not ocr_status or ocr_status.upper() == "N/A":
            return False, (
                f"OCR was not enabled for uploaded .{ext} document '{name}' "
                f"(OCR Status: {ocr_status or 'missing'})"
            )
        return True, f"Document '{name}' (.{ext}) uploaded with OCR enabled (OCR Status: {ocr_status})"

    return _scenario


SCENARIOS = [("OCR pdf", ocr("pdf")), ("OCR png", ocr("png"))]


def main() -> None:
    c.run_dms_test(TEST_CASE_ID, SCENARIOS, doc=__doc__)


if __name__ == "__main__":
    main()
