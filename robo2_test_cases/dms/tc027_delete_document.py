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
    name = info["name"]
    ok, message = session.document.delete_current()
    if not ok:
        return False, message

    if session.explorer.search_finds(name):
        return False, f"{message}. Deleted document is still found in quick search"
    if session.explorer.explorer_has(info["doc_type"], name):
        return False, f"{message}. Deleted document is still shown in explorer view"
    if not session.explorer.open_restore_page(name):
        return False, f"{message}. Deleted document '{name}' not listed on Restore page"
    return True, f"{message}. Removed from Explorer/Quick Search and listed on Restore page"


SCENARIOS = [("Delete document", delete_document)]


def main() -> None:
    c.run_dms_test(TEST_CASE_ID, SCENARIOS, doc=__doc__)


if __name__ == "__main__":
    main()
