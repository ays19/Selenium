"""
DMS-TC101
Master Table Method (Fetch)
1. Go to https://ecmv6.robo2mation.com/dms/document/settings/share_document/
2. Click on "Add Method" icon
3. Create a "Multiple Record" master table fetch method
1. Multiple record master table method should be created successfully & system should give proper confirmation message.
2. Multiple records should be set on the dropdown fields of the metadataa on upload documents, edit metadata, advanced search & my documents search
"""
import common as c

TEST_CASE_ID = "DMS-TC101"


def multiple_record(session: c.DmsSession) -> tuple[bool, str]:
    ok, message, name = session.master_table.create_method("multiple record")
    return ok, f"{message} ({name}). Dropdown values on the upload / search pages are not checked by the script"


SCENARIOS = [("Multiple record method", multiple_record)]


def main() -> None:
    c.run_dms_test(TEST_CASE_ID, SCENARIOS, doc=__doc__)


if __name__ == "__main__":
    main()
