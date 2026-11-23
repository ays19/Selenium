"""
DMS-TC026
Restore Archived Doc
1. Open a document that is checked-out
2. Click on "Restore Archive"
3. Click on "Yes, Restore"
4. Document should be restored with proper confirmation message
2. Document should be available in xplorer view
3. Document should be available in quick search
4. Document should be available in advanced search (without enabling "include archive"
"""
import common as c

TEST_CASE_ID = "DMS-TC026"


def restore_archived(session: c.DmsSession) -> tuple[bool, str]:
    info = session.new_document()
    name = info["name"]
    ok, message = session.document.archive()
    if not ok:
        raise c.SetupError(f"could not archive the test document ({message})")

    session.explorer.open()
    session.explorer.advanced_search(name, include_archive=True)
    session.explorer.open_from_advanced_search(name)

    ok, message = session.document.restore_archived()
    if not ok:
        return False, message

    missing = []
    if not session.explorer.explorer_has(info["doc_type"], name):
        missing.append("explorer view")
    if not session.explorer.search_finds(name, tries=3):
        missing.append("quick search")
    if not session.explorer.advanced_finds(name, doc_type=info["doc_type"]):
        missing.append("advanced search")
    if missing:
        return False, f"{message}. Restored document is not shown in: {', '.join(missing)}"
    return True, f"{message}. Document is available in explorer view, quick search and advanced search"


SCENARIOS = [("Restore archive", restore_archived)]


def main() -> None:
    c.run_dms_test(TEST_CASE_ID, SCENARIOS, doc=__doc__)


if __name__ == "__main__":
    main()
