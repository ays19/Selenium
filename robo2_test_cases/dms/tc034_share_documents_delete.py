"""
DMS-TC034
Share Documents (Delete)
1. Go to "Document View" page
2. Click on "Delete" button under "Share Document" section
Share documents participants should be removed & those documents no longer available for those people
"""
import common as c

TEST_CASE_ID = "DMS-TC034"


def delete_share(session: c.DmsSession) -> tuple[bool, str]:
    info = session.upload_document("pdf", share="users")
    name = info["name"]
    shared_with = info["shared_with"]

    session.explorer.open_document(name)
    ok, msg = session.document.delete_shared_participant()
    if not ok:
        return False, msg
    icons = session.explorer.explorer_doc_icons(info["doc_type"], name)
    if not icons["found"] or icons["shared"]:
        return False, f"{msg}, but Explorer shared icon still active ({icons})"
    return True, f"{msg}. Shared participant '{shared_with}' removed and Explorer shared icon cleared"


SCENARIOS = [("Delete share", delete_share)]


def main() -> None:
    c.run_dms_test(TEST_CASE_ID, SCENARIOS, doc=__doc__)


if __name__ == "__main__":
    main()
