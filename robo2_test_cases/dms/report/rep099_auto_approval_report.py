"""
REP-TC099: Auto Approval Report
1. Go to https://ecmv6.robo2mation.com/workflow/workflow_report/wf_auto_approval/
2. Sort by any column
Expected: Auto approval report should be sorted
"""
import common as c

TEST_CASE_ID = "REP-TC099"
ROUTE = "/workflow/workflow_report/wf_auto_approval/"
SORT_COLUMNS = ["any"]


def test_sort_auto_approval_report(session: c.ReportSession) -> str:
    session.login_as_role("wf_admin")
    session.open_report(ROUTE)
    return session.sort_by(SORT_COLUMNS)


if __name__ == "__main__":
    c.run_report_test(TEST_CASE_ID, ROUTE, test_sort_auto_approval_report, __doc__)