"""
DMS-TC021
Cancel Checkout Doc
1. Open a document that is checked-out
2. Click on "cancel check out"
3. Click on "Yes" button
1. Document should be checked in with proper confirmation message.
2. Check-out icon shouldn't show in explorer view for admin & the user whom do the check out.
(admin only: the second user part is not tested here)
"""
import common as c

TEST_CASE_ID = "DMS-TC021"


def cancel_check_out(session: c.DmsSession) -> tuple[bool, str]:
    info = session.new_document()
    name = info["name"]

    ok, message = session.document.check_out()
    if not ok:
        raise c.SetupError(f"could not check out the test document ({message})")

    session.explorer.open_document(name)
    ok, message = session.document.cancel_check_out()
    if not ok:
        return False, message

    still_listed = session.document.is_in_checked_out_list(name, timeout=4)
    return (not still_listed), (
        f"{message}. Removed from Checked Out Documents: {'yes' if not still_listed else 'NO'}"
    )


SCENARIOS = [("Cancel check-out", cancel_check_out)]


def main() -> None:
    c.run_dms_test(TEST_CASE_ID, SCENARIOS, doc=__doc__)


if __name__ == "__main__":
    main()
