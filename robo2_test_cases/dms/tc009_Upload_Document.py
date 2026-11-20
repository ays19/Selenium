"""
DMS-TC009
Upload Document
1. Go to https://ecmv6.robo2mation.com/dms/document/upload/standard_upload/filesave/pendingmetalist/
2. Attach a document (image, media or office file), select doc-type, give all required meta-data value & give unique value to unique field.
3. Click on "Save" button
Documents should be uploaded with proper confirmation message
"""
from datetime import datetime

import common as c

TEST_CASE_ID = "DMS-TC009"
FILES_TO_UPLOAD = ["png", "mp3", "docx"]  # image, media, office file


def upload_ext(ext: str):
    def _scenario(session: c.DmsSession) -> tuple[bool, str]:
        session.upload.prepare_upload(ext)
        session.upload.set_document_name(datetime.now().strftime(f"AUTO_{ext}_%H%M%S"))
        return session.upload.click_save_upload()

    return _scenario


def summarize(results: list[tuple[str, bool, str]]) -> str:
    total = len(results)
    passed = [f"{lbl} ({msg})" for lbl, ok, msg in results if ok]
    failed = [f"{lbl} ({msg})" for lbl, ok, msg in results if not ok]
    if failed:
        return f"Uploaded {len(passed)}/{total}. Failed: " + ", ".join(failed)
    return f"All {total} documents uploaded. Confirmation shown: " + "; ".join(passed)


SCENARIOS = [(ext, upload_ext(ext)) for ext in FILES_TO_UPLOAD]


def main() -> None:
    c.run_dms_test(TEST_CASE_ID, SCENARIOS, doc=__doc__, summary_fn=summarize)


if __name__ == "__main__":
    main()
