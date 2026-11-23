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


def _attach_pending(session: c.DmsSession, ext: str) -> str:
    sample = session.upload.find_sample_file(ext)
    if not sample:
        raise c.SetupError(f"no .{ext} sample file in {c.SAMPLE_DIR}")
    return session.upload.attach_and_get_pending_names([sample[1]])[0]


def non_ocr_doc_has_no_icon(session: c.DmsSession) -> tuple[bool, str]:
    pending_name = _attach_pending(session, "docx")
    has_icon = session.upload.has_ocr_icon(pending_name)
    if has_icon:
        return False, f"OCR icon unexpectedly appeared for non-PDF/image file '{pending_name}'"
    return True, f"Non-PDF/image file '{pending_name}' correctly has no OCR Document icon"


def ocr_pending_file(ext: str):
    def _scenario(session: c.DmsSession) -> tuple[bool, str]:
        pending_name = _attach_pending(session, ext)
        if not session.upload.has_ocr_icon(pending_name):
            return False, f"OCR Document icon (.ocr-item) not shown for pending .{ext} file '{pending_name}'"
        ok, msg = session.upload.run_pending_ocr(pending_name, timeout=60)
        if not ok:
            return False, f"Pending OCR failed for '{pending_name}': {msg}"
        return True, f"Pending OCR succeeded for .{ext} file '{pending_name}': {msg}"

    return _scenario


SCENARIOS = [
    ("Non-PDF/Image (.docx) has no OCR icon", non_ocr_doc_has_no_icon),
    ("OCR .pdf in Pending Documents", ocr_pending_file("pdf")),
    ("OCR .png in Pending Documents", ocr_pending_file("png")),
]


def main() -> None:
    c.run_dms_test(TEST_CASE_ID, SCENARIOS, doc=__doc__)


if __name__ == "__main__":
    main()
