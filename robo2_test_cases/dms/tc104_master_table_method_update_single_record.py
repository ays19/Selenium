"""
DMS-TC104
Master Table Method (Fetch)
1. Go to https://ecmv6.robo2mation.com/dms/document/settings/share_document/
2. Update a "Single Record" master table fetch method
1. Single record master table method should be updated successfully & system should give proper confirmation message.
2. When user try to upload documents, edit metadata, advanced search & my documents search then data should be fetched accordingly.
"""
import common as c

TEST_CASE_ID = "DMS-TC104"


def update(session: c.DmsSession) -> tuple[bool, str]:
    name = session.master_table.new_method("single record")
    new_name = name + "_UPD"
    ok, message = session.master_table.update_method(name, new_name)
    return ok, f"{message} ({name} -> {new_name}). Fetching on the upload / search pages is not checked by the script"


SCENARIOS = [("Update single record method", update)]


def main() -> None:
    c.run_dms_test(TEST_CASE_ID, SCENARIOS, doc=__doc__)


if __name__ == "__main__":
    main()
