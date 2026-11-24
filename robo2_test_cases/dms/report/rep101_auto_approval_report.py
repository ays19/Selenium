"""
REP-TC101: Auto Approval Report
1. Go to https://ecmv6.robo2mation.com/workflow/workflow_report/wf_auto_approval/
2. Filter by "Process" & "Status"
Expected: Only filtered data should be shown
"""
import common as c

TEST_CASE_ID = "REP-TC101"
ROUTE = "/workflow/workflow_report/wf_auto_approval/"
FILTER_LABELS = ["Process", "User"]


def test_filter_auto_approval_report(session: c.ReportSession) -> str:
    session.login_as_role("wf_admin")
    session.open_report(ROUTE)
    return session.search_or_filter(FILTER_LABELS, report_key="auto_approval")


if __name__ == "__main__":
    c.run_report_test(TEST_CASE_ID, ROUTE, test_filter_auto_approval_report, __doc__)