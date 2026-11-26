"""
CON-TC003: User Maker - Send User Approval Request & Verify Activity Report
1. Login as User with "User Maker" Permission
2. Open Users / User Approval Requests and submit a new User Approval Request
Expected: Should be able to send User Approval Requests with proper confirmation message & activity report
"""
from datetime import datetime

import common as c
import configurable_config as cfg

TEST_CASE_ID = "CON-TC003"
ROUTE = cfg.route("APPROVAL", "/admin/user/user-creation-requests/")
ACTIVITY_ROUTE = cfg.route("ACTIVITY_REPORT", "/report/activity-report/")


def test_maker_send_user_approval_request(session: c.ConfigurableSession) -> str:
    ts = datetime.now().strftime("%m%d%H%M%S")
    first_name = "Con003"
    last_name = f"Maker{ts}"
    username = f"con003_{ts}"
    email = f"con003_{ts}@example.com"
    password = "Test@123456"
    comment = f"Automated CON-TC003 approval request ({ts})"

    session.login_as_role("user_maker")
    session.open_route(ROUTE)

    with session.step("Open Add User Request form and submit new user approval request"):
        session.user_page.assert_page_header_contains("User Approval Requests")
        session.user_page.open_add_user_request_form()
        confirm_msg, selected_role = session.user_page.fill_and_submit_user_request(
            first_name=first_name,
            last_name=last_name,
            username=username,
            email=email,
            password=password,
            comment=comment,
        )
        if not confirm_msg:
            raise AssertionError("Expected a confirmation message after submitting User Approval Request.")

    with session.step("Verify new request appears in User Approval Requests list"):
        if "user-creation-requests" not in session.driver.current_url.casefold():
            session.open_route(ROUTE)
        session.user_page.assert_page_header_contains("User Approval Requests")
        session.user_page.search_table(username)
        approval_row = session.user_page.find_row_containing(username)
        if not approval_row:
            raise AssertionError(
                f"Submitted user request '{username}' was not found in User Approval Requests table."
            )

    with session.step("Verify Core Activity Report records the user approval request"):
        session.open_route(ACTIVITY_ROUTE)
        session.user_page.assert_page_header_contains("Core Activity Report")
        activity_row = (
            session.user_page.find_row_containing(username)
            or session.user_page.find_row_containing(last_name)
        )
        if not activity_row:
            session.user_page.search_table(username)
            activity_row = session.user_page.find_row_containing(username)
        if not activity_row:
            session.user_page.search_table(last_name)
            activity_row = session.user_page.find_row_containing(last_name)
        if not activity_row:
            top_rows = [r.text.strip() for r in session.user_page.visible_rows(timeout=5)[:3]]
            raise AssertionError(
                f"Expected Core Activity Report entry for '{username}' / '{last_name}'. "
                f"Top visible rows: {top_rows}"
            )

    return (
        f"Sent User Approval Request for '{username}' (role='{selected_role}'), "
        f"confirmation='{confirm_msg}', verified in User Approval Requests list and Core Activity Report."
    )


if __name__ == "__main__":
    c.run_configurable_test(TEST_CASE_ID, ROUTE, test_maker_send_user_approval_request, __doc__)
