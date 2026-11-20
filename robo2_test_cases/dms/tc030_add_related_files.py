"""
DMS-TC030
Add Related Files
1. Open a document
2. Click on "Add" icon on related files
3. Check mark all needed files
4. Click on "Link" button
Related files should be linked with proper confirmation message and should view properly
"""
import common as c

TEST_CASE_ID = "DMS-TC030"


def add_related(session: c.DmsSession) -> tuple[bool, str]:
    first = session.upload_document("pdf")
    second = session.upload_document("txt")
    session.explorer.open_document(first["name"])

    ok, message = session.document.link_related_file(second["name"])
    if not ok:
        return False, message

    shown = session.document.is_related_shown(second["name"])
    return shown, (
        f"{message}. Related file '{second['name']}' "
        + ("shown in related files" if shown else "NOT shown in related files")
    )


SCENARIOS = [("Add related file", add_related)]


def main() -> None:
    c.run_dms_test(TEST_CASE_ID, SCENARIOS, doc=__doc__)


if __name__ == "__main__":
    main()
