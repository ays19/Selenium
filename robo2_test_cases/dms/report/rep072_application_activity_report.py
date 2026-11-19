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
    session.login_as_role("wf_user")
    session.open_report(ROUTE)
    return session.verify_scope("own")


if __name__ == "__main__":
    c.run_report_test(
        TEST_CASE_ID, ROUTE, test_own_application_activity_report, __doc__
    )