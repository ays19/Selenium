"""
DMS-TC020
Check-Out Doc
1. Open a document
2. Click on check out
3. Click on "Yes" button
1. Document should be checked out with proper confirmation message.
2. A check-out icon should show in explorer view for admin & the user whom do the check out.
(admin only: the second user part is not tested here)
"""
import common as c

TEST_CASE_ID = "DMS-TC020"


def check_out(session: c.DmsSession) -> tuple[bool, str]:
    info = session.new_document()
    ok, message = session.document.check_out()
    if not ok:
        return False, message

    in_list = session.document.is_in_checked_out_list(info["name"])
    return in_list, f"{message}. Shown in Checked Out Documents: {'yes' if in_list else 'NO'}"


SCENARIOS = [("Check-out", check_out)]


def main() -> None:
    c.run_dms_test(TEST_CASE_ID, SCENARIOS, doc=__doc__)


if __name__ == "__main__":
    main()
