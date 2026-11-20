"""
DMS-TC086
Update Metadata
1. Go to https://flow.robo2mation.com/dms/document/root
2. Double click on a doc-type
3. Select a metadata
4. Click on "Update" button
5. Update metadata information
6. Click on "Save" button
Metadata should be updated with confirmation message
"""
from datetime import datetime

import common as c

TEST_CASE_ID = "DMS-TC086"


def update_metadata(session: c.DmsSession) -> tuple[bool, str]:
    doc_type = session.categorization.new_doc_type()
    display = datetime.now().strftime("AUTO Meta %H%M%S")
    ok, msg = session.categorization.create_metadata_string_form(doc_type, display)
    if not ok:
        raise c.SetupError(f"could not create initial metadata ({msg})")
    return session.categorization.update_metadata_display_name(display, display + " UPD")


SCENARIOS = [("Update metadata", update_metadata)]


def main() -> None:
    c.run_dms_test(TEST_CASE_ID, SCENARIOS, doc=__doc__)


if __name__ == "__main__":
    main()
