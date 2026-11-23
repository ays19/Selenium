"""
DMS-TC019
Edit Metadata
1. Open a document
2. Click on on edit metadata
3. Update necessary meta data
4. Click on "Save Changes" button
Metadata should be updated with proper confirmation message
"""
import common as c

TEST_CASE_ID = "DMS-TC019"


def edit_metadata(session: c.DmsSession) -> tuple[bool, str]:
    session.new_document()
    return session.document.edit_metadata_field_and_save()


SCENARIOS = [("Edit metadata", edit_metadata)]


def main() -> None:
    c.run_dms_test(TEST_CASE_ID, SCENARIOS, doc=__doc__)


if __name__ == "__main__":
    main()
