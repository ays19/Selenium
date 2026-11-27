"""
CON-TC023: User with both "Maker & Checker" Permissions
Expected: Should be able to send User Approval Requests & approve/reject request.
"""
import time
import common as c
import configurable_config as cfg

TEST_CASE_ID = "CON-TC023"
ROUTE = cfg.route("APPROVAL", "/admin/user/approval-requests/")


def test_maker_and_checker_permissions(session: c.ConfigurableSession) -> str:
    ts = int(time.time()) % 100000
    temp_user = f"qa_mc_{ts}"

    session.login_as_role("maker_checker")
    session.open_route(ROUTE)

    with session.step(f"Create user approval request '{temp_user}' as Maker & Checker"):
        create_msg = session.user_page.create_user_request(
            temp_user, "QaTest@1234", f"{temp_user}@example.com"
        )

    session.open_route(ROUTE)
    with session.step(f"Reject (or approve) request '{temp_user}' using same Maker & Checker account"):
        session.user_page.search_table(temp_user)
        session.user_page.select_row_by_text(temp_user)
        action_msg = session.user_page.reject_selected_request("Maker+Checker self-verification (CON-TC023)")

    return f"Maker & Checker user created ('{create_msg}') and processed ('{action_msg}') request '{temp_user}'."


if __name__ == "__main__":
    c.run_configurable_test(TEST_CASE_ID, ROUTE, test_maker_and_checker_permissions, __doc__)