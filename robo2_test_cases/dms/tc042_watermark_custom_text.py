"""
DMS-TC042
Watermark (Custom Text)
1. Go to https://ecmv6.robo2mation.com/dms/document/upload/standard_upload/filesave/pendingmetalist/
2. Select a document type
3. Click on "Watermark File" field
4. Go to "Custom Text"
5. Type watermark text (max: 20 character)
6. Click on "Create"
Watermark should be created with proper confirmation message.
"""
from datetime import datetime

import common as c

TEST_CASE_ID = "DMS-TC042"


def custom_text(session: c.DmsSession) -> tuple[bool, str]:
    session.upload.prepare_upload("pdf")
    text = datetime.now().strftime("AUTO_WM_%H%M%S")  # max 20 characters
    return session.upload.create_text_watermark(text)


SCENARIOS = [("Custom text watermark", custom_text)]


def main() -> None:
    c.run_dms_test(TEST_CASE_ID, SCENARIOS, doc=__doc__)


if __name__ == "__main__":
    main()
