"""
REP-TC098: Auto Approval Report
1. Go to https://ecmv6.robo2mation.com/workflow/workflow_report/wf_auto_approval/
2. Search by "Project", "App Number", "User" & "Status"
Expected: Only searched data should be shown
"""
import common as c

TEST_CASE_ID = "REP-TC098"
ROUTE = "/workflow/workflow_report/wf_auto_approval/"
SEARCH_LABELS = ["Project", "App Number", "User"]


def test_search_auto_approval_report(session: c.ReportSession) -> str:
    session.login_as_role("wf_admin")
    session.open_report(ROUTE)
    return session.search_or_filter(SEARCH_LABELS, report_key="auto_approval")


if __name__ == "__main__":
    c.run_report_test(TEST_CASE_ID, ROUTE, test_search_auto_approval_report, __doc__)