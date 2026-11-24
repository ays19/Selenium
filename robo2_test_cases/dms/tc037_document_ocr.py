"""
DMS-TC037
Document OCR
1. Go to https://ecmv6.robo2mation.com/dms/document/upload/standard_upload/
2. Try to attach a doc apart from pdf or image (jpg,jpeg or png)
3. Try to click on "OCR Document" icon
Document ocr should be done.
"""
import os

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


def ocr_uploaded_file(ext: str):
    def _scenario(session: c.DmsSession) -> tuple[bool, str]:
        doc_type = os.getenv("OCR_DOC_TYPE", "").strip()
        ocr_timeout = int(os.getenv("OCR_TIMEOUT", "65"))
        info = session.upload_document(ext, doc_type=doc_type)
        ok, status_msg = session.open_and_wait_for_ocr(info["name"], timeout_seconds=ocr_timeout)
        if not ok:
            return False, f"{status_msg} for .{ext} file '{info['name']}'"
        return True, f"OCR completed for .{ext} file '{info['name']}' in '{info['doc_type']}' ({status_msg})"

    return _scenario


SCENARIOS = [
    ("Non-PDF/Image (.docx) has no OCR icon", non_ocr_doc_has_no_icon),
    ("OCR .pdf document", ocr_uploaded_file("pdf")),
    ("OCR .png document", ocr_uploaded_file("png")),
]


def main() -> None:
    c.run_dms_test(
        TEST_CASE_ID,
        SCENARIOS,
        doc=__doc__,
        required_env=[("OCR_DOC_TYPE", "(search text of a doc-type with OCR enabled)")],
    )


if __name__ == "__main__":
    main()
