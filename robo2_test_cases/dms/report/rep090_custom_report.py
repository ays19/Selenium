"""
REP-TC090: Custom Report
1. Go to https://ecmv6.robo2mation.com/workflow/workflow_report/general_report
2. Search by "Project", "App Number", "User" & "Status"
Expected: Only searched data should be shown
"""
import common as c

TEST_CASE_ID = "REP-TC090"
ROUTE = "/workflow/workflow_report/general_report"
REPORT_NAME = "Default Variable Report"
SEARCH_LABELS = ["App Number", "User", "Status"]


def test_search_custom_report(session: c.ReportSession) -> str:
    session.login_as_role("wf_admin")
    session.open_custom_report(ROUTE, report_name=REPORT_NAME)
    return session.search_or_filter(SEARCH_LABELS, report_key="custom_report")


if __name__ == "__main__":
    c.run_report_test(TEST_CASE_ID, ROUTE, test_search_custom_report, __doc__)