"""
CON-TC005: User Maker - Send User Update Request After Approval
1. Login as User with "User Maker" Permission
2. Open Users panel (approved users list) and select an approved user
3. Click "Edit User", update user info, and submit
4. Verify confirmation message and Activity Report entry
Expected: Should be able to send user update request after approval, with proper confirmation message & activity report.
"""
import common as c
import configurable_config as cfg

TEST_CASE_ID = "CON-TC005"
ROUTE = cfg.route("USERS", "/admin/user/list")
ACTIVITY_ROUTE = cfg.route("ACTIVITY_REPORT", "/report/activity-report/")


def test_maker_update_request_after_approval(session: c.ConfigurableSession) -> str:
    session.login_as_role("user_maker")
    session.open_route(ROUTE)

    # Optionally target a specific approved username from .env.configurable; otherwise pick the first row
    target_user = cfg.env_value("APPROVED_USER_USERNAME", "")

    with session.step(
        f"Select approved user ('{target_user or 'first visible row'}') in Users list"
    ):
        if target_user:
            session.user_page.search_table(target_user)
        session.user_page.select_row_by_text(target_user)

    with session.step("Edit approved user details and submit update request"):
        confirmation_msg = session.user_page.edit_selected_user_and_submit()

    with session.step("Verify update request is recorded in Core Activity Report"):
        maker_username = cfg.get_profile("user_maker").username
        matched_kw = session.user_page.assert_activity_logged(
            session.base_url,
            ACTIVITY_ROUTE,
            expected_keywords=[
                target_user,
                maker_username,
                "update",
                "user",
            ],
        )

    return (
        f"Submitted update request after approval for '{target_user or 'selected user'}'. "
        f"Confirmation: '{confirmation_msg}' | Activity Report matched: '{matched_kw}'."
    )


if __name__ == "__main__":
    c.run_configurable_test(
        TEST_CASE_ID, ROUTE, test_maker_update_request_after_approval, __doc__
    )