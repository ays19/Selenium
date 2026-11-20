"""
DMS-TC024
Document Full View
1. Open a document
2. Click on "view"
Document should be opened in a new tab
"""
import common as c

TEST_CASE_ID = "DMS-TC024"


def full_view(session: c.DmsSession) -> tuple[bool, str]:
    session.new_document()
    url = session.document.open_full_view_tab()
    return True, f"Document opened in a new tab ({url})"


SCENARIOS = [("Full view", full_view)]


def main() -> None:
    c.run_dms_test(TEST_CASE_ID, SCENARIOS, doc=__doc__)


if __name__ == "__main__":
    main()
