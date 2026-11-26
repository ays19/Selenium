"""
CON-TC011: User Checker - Approve/Reject User Approval & Update Requests
1. Login as User with "User Checker" Permission
2. Approve or reject a pending User Approval / Update request
Expected: Should be able to approve/reject User Approval Requests, user update request with proper confirmation message & activity report.
"""
import common as c
import configurable_config as cfg

TEST_CASE_ID = "CON-TC011"
ROUTE = cfg.route("APPROVAL", "/admin/user/approval-requests/")
ACTIVITY_ROUTE = cfg.route("ACTIVITY_REPORT", "/report/activity-report/")


def test_checker_approve_reject_requests(session: c.ConfigurableSession) -> str:
    session.login_as_role("user_checker")
    session.open_route(ROUTE)

    target = cfg.env_value("CHECKER_ACTION_USERNAME", "Pending")
    action = cfg.env_value("CHECKER_TC011_ACTION", "approve").lower()

    with session.step(f"Select pending request ('{target}') and {action}"):
        if target.casefold() != "pending":
            session.user_page.search_table(target)
        session.user_page.select_row_by_text(target)
        if action == "reject":
            msg = session.user_page.reject_selected_request("QA Checker rejection (CON-TC011)")
        else:
            msg = session.user_page.approve_selected_request()

    with session.step("Verify action is logged in Core Activity Report"):
        checker_user = cfg.get_profile("user_checker").username
        matched = session.user_page.assert_activity_logged(
            session.base_url, ACTIVITY_ROUTE, [checker_user, action, "user"]
        )

    return f"Checker {action}d request ('{target}'). Confirmation: '{msg}' | Activity matched: '{matched}'."


if __name__ == "__main__":
    c.run_configurable_test(TEST_CASE_ID, ROUTE, test_checker_approve_reject_requests, __doc__)