"""
DMS-TC031
Delete Related Files
1. Open a document
2. Click on related files
3. Click on "Delete" icon
4. Click on "Yes, Unlink" button
Related files should be unlinked with proper confirmation message
"""
import common as c

TEST_CASE_ID = "DMS-TC031"


def delete_related(session: c.DmsSession) -> tuple[bool, str]:
    first = session.upload_document("pdf")
    second = session.upload_document("txt")
    session.explorer.open_document(first["name"])

    ok, message = session.document.link_related_file(second["name"])
    if not ok:
        raise c.SetupError(f"could not link the related file ({message})")

    ok, message = session.document.unlink_related_file(second["name"])
    if not ok:
        return False, message

    session.document.expand_related_panel()
    gone = not session.document.wait_text(second["name"], 3)
    return gone, f"{message}. Related file " + (
        "removed from the list" if gone else "still shown in the list"
    )


SCENARIOS = [("Delete related file", delete_related)]


def main() -> None:
    c.run_dms_test(TEST_CASE_ID, SCENARIOS, doc=__doc__)


if __name__ == "__main__":
    main()
