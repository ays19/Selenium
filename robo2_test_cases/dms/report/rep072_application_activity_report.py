"""
REP-TC072: Application Activity Report
1. Go to https://ecmv6.robo2mation.com/workflow/workflow_report/overall_monitor/
2. User's without "All Process Information" & "Related Process Information"
Expected: Should see his/her participated applications
"""
import common as c

TEST_CASE_ID = "REP-TC072"
ROUTE = "/workflow/workflow_report/overall_monitor/"


def test_own_application_activity_report(session: c.ReportSession) -> str:
    session.login_as_role("wf_admin")
    session.open_report(ROUTE)
    admin_count = session.report_page.assert_has_rows("wf_admin baseline")

    username = session.login_as_role("wf_user")
    session.open_report(ROUTE)
    with session.step(
        f"Verify '{username}' sees own participated applications (restricted vs admin)"
    ):
        session.report_page.assert_table_contains(username, "own participated application")
        own_count = session.report_page.row_count()
        if own_count >= admin_count:
            raise AssertionError(
                f"Expected restricted application list for '{username}', "
                f"but saw {own_count} row(s) vs admin's {admin_count}."
            )
    return (
        f"Role 'wf_user': sees own participated applications for '{username}' "
        f"({own_count} row(s) vs admin's {admin_count})."
    )


if __name__ == "__main__":
    c.run_report_test(
        TEST_CASE_ID, ROUTE, test_own_application_activity_report, __doc__
    )