"""
DMS-TC046
Search Water Mark
1. Go to https://ecmv6.robo2mation.com/dms/document/upload/standard_upload/filesave/pendingmetalist/
2. Select a document type
3. Click on "Watermark File" field
4. Go to "Public Library" or "Private Library" tab
5. Search by filename
Only searched result should be shown
"""
from datetime import datetime

import common as c

TEST_CASE_ID = "DMS-TC046"


def search_watermark(session: c.DmsSession) -> tuple[bool, str]:
    session.upload.prepare_upload("pdf")
    run_id = datetime.now().strftime("%H%M%S")
    wanted, other = f"AUTO_WM_A{run_id}", f"AUTO_WM_B{run_id}"
    for text in (wanted, other):
        ok, message = session.upload.create_text_watermark(text)
        if not ok:
            raise c.SetupError(f"could not create watermark '{text}' ({message})")

    return session.upload.search_watermark_library(wanted, other)


SCENARIOS = [("Search watermark", search_watermark)]


def main() -> None:
    c.run_dms_test(TEST_CASE_ID, SCENARIOS, doc=__doc__)


if __name__ == "__main__":
    main()
