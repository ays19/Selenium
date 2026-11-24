"""
REP-TC100: Auto Approval Report
1. Go to https://ecmv6.robo2mation.com/workflow/workflow_report/wf_auto_approval/
2. Select a date range
Expected: Only selected dates data should be shown
"""
import common as c

TEST_CASE_ID = "REP-TC100"
ROUTE = "/workflow/workflow_report/wf_auto_approval/"


def test_date_range_auto_approval_report(session: c.ReportSession) -> str:
    session.login_as_role("wf_admin")
    session.open_report(ROUTE)
    return session.filter_by_date()


if __name__ == "__main__":
    c.run_report_test(TEST_CASE_ID, ROUTE, test_date_range_auto_approval_report, __doc__)