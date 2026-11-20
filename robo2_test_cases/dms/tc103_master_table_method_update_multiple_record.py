"""
DMS-TC103
Master Table Method (Fetch)
1. Go to https://ecmv6.robo2mation.com/dms/document/settings/share_document/
2. Update a "Multiple Record" master table fetch method
1. Multiple record master table method should be updated successfully & system should give proper confirmation message.
2. Multiple records should be set on the dropdown fields of the metadataa on upload documents, edit metadata, advanced search & my documents search
"""
import common as c

TEST_CASE_ID = "DMS-TC103"


def update(session: c.DmsSession) -> tuple[bool, str]:
    name = session.master_table.new_method("multiple record")
    new_name = name + "_UPD"
    ok, message = session.master_table.update_method(name, new_name)
    return ok, f"{message} ({name} -> {new_name}). Dropdown values on the upload / search pages are not checked by the script"


SCENARIOS = [("Update multiple record method", update)]


def main() -> None:
    c.run_dms_test(TEST_CASE_ID, SCENARIOS, doc=__doc__)


if __name__ == "__main__":
    main()
