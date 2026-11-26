"""
CON-TC020: Pending User Update Request
Expected:
i) User should be able to login with valid credentials, but information shouldn't be updated (Login Report, Update User Profile)
ii) Should be available on "Users" list
"""
import common as c
import configurable_config as cfg

TEST_CASE_ID = "CON-TC020"
ROUTE = cfg.route("USERS", "/admin/user/list")


def test_pending_user_update_request(session: c.ConfigurableSession) -> str:
    target_user = cfg.env_value("UPDATE_FLOW_USERNAME")
    target_pass = cfg.env_value("UPDATE_FLOW_PASSWORD")
    if not target_user or not target_pass:
        raise RuntimeError("Set UPDATE_FLOW_USERNAME and UPDATE_FLOW_PASSWORD in .env.configurable.")

    pending_val = f"PendingEdit_{cfg.env_value('RUN_TAG', 'TC020')}"

    session.login_as_role("user_maker")
    session.open_route(ROUTE)
    with session.step(f"Submit pending update request for '{target_user}'"):
        session.user_page.search_table(target_user)
        session.user_page.select_row_by_text(target_user)
        session.user_page.edit_selected_user_and_submit(updated_value=pending_val)

    with session.step(f"Verify '{target_user}' remains available on Users list"):
        session.open_route(ROUTE)
        session.user_page.assert_user_presence(target_user, should_exist=True)

    session.login_page.logout_if_needed(session.base_url)
    with session.step(f"Verify '{target_user}' can still login and pending edit is NOT yet applied"):
        session.login_page.login_expect_success(session.base_url, target_user, target_pass)
        session.open_route(cfg.route("LOGIN_REPORT", "/report/login_report/"))
        if pending_val.casefold() in session.user_page.body_text().casefold():
            raise AssertionError(f"Pending update value '{pending_val}' was applied before approval!")

    return f"Pending update for '{target_user}' did not apply before approval; user remains on Users list and can login."


if __name__ == "__main__":
    c.run_configurable_test(TEST_CASE_ID, ROUTE, test_pending_user_update_request, __doc__)