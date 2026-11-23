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
    if session.upload.selected_count() != 2:
        return False, f"expected 2 selected PDFs, got {session.upload.selected_count()}"

    session.upload.fill_metadata_form()
    if session.upload.has_visible_checker():
        raise c.SetupError(
            f"Doc type '{session.upload.current_doc_type()}' has Maker-Checker enabled; configure a non-checker DOC_TYPE"
        )
    merged_name = datetime.now().strftime("AUTO_MERGE_%H%M%S")
    session.upload.set_document_name(merged_name)

    ok, message = session.upload.click_save_upload()
    if not ok:
        return False, message
    if not session.explorer.search_finds(merged_name, tries=5):
        return False, f"Merged upload showed '{message}' but '{merged_name}' was not found in Quick Search"
    names = " + ".join(os.path.basename(p) for p in paths)
    return True, f"{names} uploaded together as '{merged_name}': {message} (found in Quick Search)"


def images_not_merged(session: c.DmsSession) -> tuple[bool, str]:
    """Scenario 2: Two images must not be selectable together."""
    sample = session.upload.find_sample_file("png") or session.upload.find_sample_file("jpg") or session.upload.find_sample_file("jpeg")
    if not sample:
        return False, "need an image file (png, jpg or jpeg) in test_files"

    pending_names = session.upload.attach_and_get_pending_names([sample[1], sample[1]])
    session.upload.open_pending_list()
    session.upload.clear_selected_files()
    if not session.upload.click_pending_icon(pending_names[0]):
        raise c.SetupError(f"could not select first image '{pending_names[0]}'")
    session.upload.wait.until(lambda _d: session.upload.selected_count() == 1)

    ok, said = session.upload.message_after(lambda: session.upload.click_pending_icon(pending_names[1]))
    count = session.upload.selected_count()
    session.upload.clear_selected_files()

    if not ok and count == 1:
        return True, f"only 1 image accepted; page rejected 2nd image: {said}"
    return False, f"expected rejection with 1 selected image; got ok={ok}, count={count}, message='{said}'"


SCENARIOS = [
    ("PDFs together", merge_pdfs),
    ("Images together", images_not_merged),
]


def main() -> None:
    c.run_dms_test(TEST_CASE_ID, SCENARIOS, doc=__doc__)


if __name__ == "__main__":
    main()
