"""
DMS-TC050
Delete Watermark
1. Go to https://ecmv6.robo2mation.com/dms/document/upload/standard_upload/filesave/pendingmetalist/
2. Select a document type
3. Click on "Watermark File" field
4. Go to "Public Library" or "Private Library" tab
5. Click on "Delete" icon
Watermark should be deleted with proper confirmation message
"""
from datetime import datetime

import common as c

TEST_CASE_ID = "DMS-TC050"


def delete_watermark(session: c.DmsSession) -> tuple[bool, str]:
    session.upload.prepare_upload("pdf")
    text = datetime.now().strftime("AUTO_WM_%H%M%S")
    ok, message = session.upload.create_text_watermark(text)
    if not ok:
        raise c.SetupError(f"could not create watermark ({message})")

    return session.upload.delete_watermark_from_library(text)


SCENARIOS = [("Delete watermark", delete_watermark)]


def main() -> None:
    c.run_dms_test(TEST_CASE_ID, SCENARIOS, doc=__doc__)


if __name__ == "__main__":
    main()
