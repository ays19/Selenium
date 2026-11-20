"""
DMS-TC033
Share Documents (External Share)
1. Go to "Pending Documents/Document View" page
2. Select public
3. Click on "Share" button
Documents should be shared with all system users & anyone with the link can access those documents.
"""
import common as c

TEST_CASE_ID = "DMS-TC033"


def share_public(session: c.DmsSession) -> tuple[bool, str]:
    info = session.upload_document("pdf", share="public")
    name = info["name"]

    if not session.explorer.search_finds(name, tries=3):
        return False, f"Uploaded as '{info['shared_with']}', but document '{name}' was not found in search"

    session.explorer.open_document(name)
    session.document.expand_share_section()
    return True, f"Document '{name}' uploaded and shared externally as '{info['shared_with']}' successfully"


SCENARIOS = [("Public share", share_public)]


def main() -> None:
    c.run_dms_test(TEST_CASE_ID, SCENARIOS, doc=__doc__)


if __name__ == "__main__":
    main()
