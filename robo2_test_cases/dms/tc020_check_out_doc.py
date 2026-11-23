"""
DMS-TC020
Check-Out Doc
1. Open a document
2. Click on check out
3. Click on "Yes" button
1. Document should be checked out with proper confirmation message.
2. A check-out icon should show in explorer view for admin & the user whom do the check out.
"""
import common as c

TEST_CASE_ID = "DMS-TC020"


def check_out(session: c.DmsSession) -> tuple[bool, str]:
    info = session.new_document()
    name = info["name"]
    ok, message = session.document.check_out()
    if not ok:
        return False, message

    in_list = session.document.is_in_checked_out_list(name)
    icons = session.explorer.explorer_doc_icons(info["doc_type"], name)
    passed = in_list and icons["found"] and icons["locked"]
    return passed, (
        f"{message}. Shown in Checked Out Documents: {'yes' if in_list else 'NO'}. "
        f"Explorer checkout lock icon: {'yes' if icons['locked'] else 'NO'}"
    )


SCENARIOS = [("Check-out", check_out)]


def main() -> None:
    c.run_dms_test(TEST_CASE_ID, SCENARIOS, doc=__doc__)


if __name__ == "__main__":
    main()
