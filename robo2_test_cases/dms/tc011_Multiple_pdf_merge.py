"""
DMS-TC011
Multiple Doc Upload Together (Document Merge)
1. Go to https://ecmv6.robo2mation.com/dms/document/upload/standard_upload/filesave/pendingmetalist/
2. Attach 2 or more documents (image, or pdf) of similar type together
3. Click on "Save" button
Only PDF documents should be merged
"""
from datetime import datetime
import os

import common as c

TEST_CASE_ID = "DMS-TC011"


def merge_pdfs(session: c.DmsSession) -> tuple[bool, str]:
    """Scenario 1: Attach and select 2 PDFs together, fill metadata, and upload."""
    paths = session.upload.pick_sample_files(["pdf"], 2)
    if not paths:
        return False, "need 2 PDF files in test_files"

    pending_names = session.upload.attach_and_get_pending_names(paths)
    session.upload.select_pending_files(pending_names)
    if session.upload.selected_count() < 2:
        return False, f"only {session.upload.selected_count()} of 2 PDFs could be selected together"

    session.upload.fill_metadata_form()
    if session.upload.has_visible_checker():
        session.upload.select_checker()
    session.upload.set_document_name(datetime.now().strftime("AUTO_MERGE_%H%M%S"))

    ok, message = session.upload.click_save_upload()
    names = " + ".join(os.path.basename(p) for p in paths)
    return ok, f"{names} uploaded together: {message}"


def images_not_merged(session: c.DmsSession) -> tuple[bool, str]:
    """Scenario 2: Two images must not be selectable together."""
    paths = session.upload.pick_sample_files(["png", "jpg", "jpeg"], 2)
    if not paths:
        return False, "need 2 image files (png, jpg or jpeg) in test_files"

    pending_names = session.upload.attach_and_get_pending_names(paths)
    session.upload.select_pending_files(pending_names)
    count = session.upload.selected_count()
    said = " ".join(session.upload.popup_text().split())
    session.upload.clear_selected_files()

    if count < 2:
        return True, f"only {count} image accepted. Page said: {said or 'nothing'}"
    return False, "both images were accepted together, so they could be merged"


SCENARIOS = [
    ("PDFs together", merge_pdfs),
    ("Images together", images_not_merged),
]


def main() -> None:
    c.run_dms_test(TEST_CASE_ID, SCENARIOS, doc=__doc__)


if __name__ == "__main__":
    main()
