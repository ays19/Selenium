"""
DMS-TC105
Master Table Method (Fetch)
1. Go to https://ecmv6.robo2mation.com/dms/document/settings/share_document/
2. Delete a master table fetch method
1. Master table method should be deleted & system should give proper confirmation message.
2. Single record won't be fetched & multiple record won't be set for the deleted methods.
"""
import common as c

TEST_CASE_ID = "DMS-TC105"


def delete_method(session: c.DmsSession) -> tuple[bool, str]:
    name = session.master_table.new_method()
    ok, message = session.master_table.delete_method(name)
    return ok, f"{message} ({name}). Fetching on the upload / search pages is not checked by the script"


SCENARIOS = [("Delete method", delete_method)]


def main() -> None:
    c.run_dms_test(TEST_CASE_ID, SCENARIOS, doc=__doc__)


if __name__ == "__main__":
    main()
