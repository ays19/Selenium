"""
DMS-TC025
Archive Doc
1. Open a document
2. Click on "Archive"
3. Click on "Yes, Archive"
1. Document should be archived with proper confirmation message
2. Document should be removed from explorer view
3. Document should be removed from quick search
4. Document should be removed from advanced search (without enabling "include archive"
"""
import common as c

TEST_CASE_ID = "DMS-TC025"


def archive(session: c.DmsSession) -> tuple[bool, str]:
    info = session.new_document()
    name = info["name"]
    ok, message = session.document.archive()
    if not ok:
        return False, message

    still_shown = []
    if session.explorer.explorer_has(info["doc_type"], name):
        still_shown.append("explorer view")
    if session.explorer.search_finds(name):
        still_shown.append("quick search")
    if session.explorer.advanced_finds(name, doc_type=info["doc_type"]):
        still_shown.append("advanced search")
    if still_shown:
        return False, f"{message}. Archived document is still shown in: {', '.join(still_shown)}"
    return True, f"{message}. Document removed from explorer view, quick search and advanced search"


SCENARIOS = [("Archive", archive)]


def main() -> None:
    c.run_dms_test(TEST_CASE_ID, SCENARIOS, doc=__doc__)


if __name__ == "__main__":
    main()
