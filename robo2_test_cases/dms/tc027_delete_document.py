"""
DMS-TC027
Delete Document
1. Open a document
2. Click on "Delete"
3. Click on "Yes, Delete"
Document should be deleted
"""
import common as c

TEST_CASE_ID = "DMS-TC027"


def delete_document(session: c.DmsSession) -> tuple[bool, str]:
    info = session.new_document()
    ok, message = session.document.delete_current()
    if not ok:
        return False, message

    if session.explorer.search_finds(info["name"]):
        return False, f"{message}. Deleted document is still found in quick search"
    return True, f"{message}. Document is not found in quick search any more"


SCENARIOS = [("Delete document", delete_document)]


def main() -> None:
    c.run_dms_test(TEST_CASE_ID, SCENARIOS, doc=__doc__)


if __name__ == "__main__":
    main()
