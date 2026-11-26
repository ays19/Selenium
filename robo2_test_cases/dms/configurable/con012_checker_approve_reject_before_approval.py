"""
CON-TC012: User Checker - Approve/Reject Request Before Approval
1. Login as User with "User Checker" Permission
2. Select a pending request (before approval) and reject with mandatory comment (or approve)
Expected: Should be able to approve/reject request before approval, with proper confirmation message & activity report.
"""
import common as c
import configurable_config as cfg

TEST_CASE_ID = "CON-TC012"
ROUTE = cfg.route("APPROVAL", "/admin/user/approval-requests/")
ACTIVITY_ROUTE = cfg.route("ACTIVITY_REPORT", "/report/activity-report/")


def test_checker_action_before_approval(session: c.ConfigurableSession) -> str:
    session.login_as_role("user_checker")
    session.open_route(ROUTE)

    target = cfg.env_value("PENDING_REQUEST_USERNAME", "Pending")
    with session.step(f"Select pending request ('{target}') before approval and reject with comment"):
        if target.casefold() != "pending":
            session.user_page.search_table(target)
        session.user_page.select_row_by_text(target)
        msg = session.user_page.reject_selected_request("Rejected before approval (CON-TC012)")

    with session.step("Verify rejection is logged in Core Activity Report"):
        checker_user = cfg.get_profile("user_checker").username
        matched = session.user_page.assert_activity_logged(
            session.base_url, ACTIVITY_ROUTE, [checker_user, "reject", "user"]
        )

    return f"Rejected pending request before approval. Confirmation: '{msg}' | Activity: '{matched}'."


if __name__ == "__main__":
    c.run_configurable_test(TEST_CASE_ID, ROUTE, test_checker_action_before_approval, __doc__)