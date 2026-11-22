"""
REP-TC087: Custom Report
1. Go to https://ecmv6.robo2mation.com/workflow/workflow_report/general_report
2. User's without "All Process Information" & "Related Process Information"
Expected: Should see his/her participated applications
"""
import common as c

TEST_CASE_ID = "REP-TC087"
ROUTE = "/workflow/workflow_report/general_report"


def test_own_custom_report(session: c.ReportSession) -> str:
    session.login_as_role("wf_user")
    session.open_custom_report(ROUTE)
    return session.verify_scope("own")


if __name__ == "__main__":
    c.run_report_test(TEST_CASE_ID, ROUTE, test_own_custom_report, __doc__)