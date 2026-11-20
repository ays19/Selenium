"""
DMS-TC085
Create Metadata
1. Go to https://ecmv6.robo2mation.com/dms/document/root
2. Double click on a doc-type
3. Click on "Add" button
4. Give "name(variable name), "display name", order & data type
5. Give option in "Dropdown Value" for drop-down data type
6. Click on "Save" button
Metadata should be created with confirmation message
"""
from datetime import datetime

import common as c

TEST_CASE_ID = "DMS-TC085"


def create_metadata(session: c.DmsSession) -> tuple[bool, str]:
    doc_type = session.categorization.new_doc_type()
    display = datetime.now().strftime("AUTO Meta %H%M%S")
    return session.categorization.create_metadata_string_form(doc_type, display)


SCENARIOS = [("Create metadata", create_metadata)]


def main() -> None:
    c.run_dms_test(TEST_CASE_ID, SCENARIOS, doc=__doc__)


if __name__ == "__main__":
    main()
