"""
CON-TC004: User Maker - Send User Update Request Before Approval
1. Login as User with "User Maker" Permission
2. Open User Approval Requests panel and select a pending user request
3. Click "Edit User", update user info, and submit
4. Verify confirmation message and Activity Report entry
Expected: Should be able to send user update request before approval, with proper confirmation message & activity report.
"""
import common as c
import configurable_config as cfg

TEST_CASE_ID = "CON-TC004"
ROUTE = cfg.route("APPROVAL", "/admin/user/user-creation-requests/")
ACTIVITY_ROUTE = cfg.route("ACTIVITY_REPORT", "/report/activity-report/")


def test_maker_update_request_before_approval(session: c.ConfigurableSession) -> str:
    session.login_as_role("user_maker")
    session.open_route(ROUTE)

    # Optionally target a specific pending username from .env.configurable; otherwise pick the first "Pending" row
    target_pending = cfg.env_str("PENDING_REQUEST_USERNAME", default="Pending")

    with session.step(f"Select pending user request ('{target_pending}') in User Approval Requests"):
        if target_pending.casefold() != "pending":
            session.user_page.search_table(target_pending)
        session.user_page.select_row_by_text(target_pending)

    with session.step("Edit pending user details and submit update request"):
        confirmation_msg = session.user_page.edit_selected_user_and_submit()

    with session.step("Verify update request is recorded in Core Activity Report"):
        maker_username = cfg.get_profile("user_maker").username
        matched_kw = session.user_page.assert_activity_logged(
            session.base_url,
            ACTIVITY_ROUTE,
            expected_keywords=[
                maker_username,
                "update",
                "user",
            ],
        )

    return (
        f"Submitted update request before approval. "
        f"Confirmation: '{confirmation_msg}' | Activity Report matched: '{matched_kw}'."
    )


if __name__ == "__main__":
    c.run_configurable_test(
        TEST_CASE_ID, ROUTE, test_maker_update_request_before_approval, __doc__
    )