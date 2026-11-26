"""
CON-TC021: Approve User Update Request
Expected:
i) User should be able to login with valid credentials and information should be updated (Login Report, Update User Profile)
ii) Should be available on "Users" list
"""
import time
import common as c
import configurable_config as cfg

TEST_CASE_ID = "CON-TC021"
ROUTE = cfg.route("APPROVAL", "/admin/user/approval-requests/")


def test_approve_user_update_request(session: c.ConfigurableSession) -> str:
    target_user = cfg.env_value("UPDATE_FLOW_USERNAME")
    target_pass = cfg.env_value("UPDATE_FLOW_PASSWORD")
    if not target_user or not target_pass:
        raise RuntimeError("Set UPDATE_FLOW_USERNAME and UPDATE_FLOW_PASSWORD in .env.configurable.")

    updated_val = f"ApprovedEdit{int(time.time()) % 10000}"

    session.login_as_role("user_maker")
    session.open_route(cfg.route("USERS", "/admin/user/list"))
    with session.step(f"Maker submits update request ('{updated_val}') for '{target_user}'"):
        session.user_page.search_table(target_user)
        session.user_page.select_row_by_text(target_user)
        session.user_page.edit_selected_user_and_submit(updated_value=updated_val)

    session.login_as_role("user_checker")
    session.open_route(ROUTE)
    with session.step(f"Checker approves update request for '{target_user}'"):
        session.user_page.search_table(target_user)
        session.user_page.select_row_by_text(target_user)
        msg = session.user_page.approve_selected_request()

    with session.step(f"Verify '{target_user}' is on Users list with updated info"):
        session.open_route(cfg.route("USERS", "/admin/user/list"))
        session.user_page.assert_user_presence(target_user, should_exist=True)
        if updated_val.casefold() not in session.user_page.body_text().casefold():
            raise AssertionError(f"Approved update value '{updated_val}' not reflected in Users list.")

    session.login_page.logout_if_needed(session.base_url)
    with session.step(f"Verify '{target_user}' can login with updated profile"):
        session.login_page.login_expect_success(session.base_url, target_user, target_pass)

    return f"Approved update ('{updated_val}') for '{target_user}' applied and login verified. Msg: '{msg}'."


if __name__ == "__main__":
    c.run_configurable_test(TEST_CASE_ID, ROUTE, test_approve_user_update_request, __doc__)