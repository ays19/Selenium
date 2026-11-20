"""
DMS-TC028
Restore Deleted Doc
1. Go to https://ecmv6.robo2mation.com/dms/restore/
2. Click on "Restore" button
Document should be restored with proper confirmation message
"""
import common as c

TEST_CASE_ID = "DMS-TC028"


def restore_deleted(session: c.DmsSession) -> tuple[bool, str]:
    info = session.new_document()
    name = info["name"]
    ok, message = session.document.delete_current()
    if not ok:
        raise c.SetupError(f"could not delete the test document ({message})")

    if not session.explorer.open_restore_page(name):
        return False, f"'{name}' not listed on the Restore Documents page"

    ok, message = session.explorer.restore_deleted_document(name)
    if not ok:
        return False, message

    found = session.explorer.search_finds(name, tries=3)
    return found, f"{message}. Document " + (
        "found in quick search again" if found else "NOT found in quick search after restore"
    )


SCENARIOS = [("Restore deleted", restore_deleted)]


def main() -> None:
    c.run_dms_test(TEST_CASE_ID, SCENARIOS, doc=__doc__)


if __name__ == "__main__":
    main()
