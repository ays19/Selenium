"""
REP-TC092: Custom Report
1. Go to https://ecmv6.robo2mation.com/workflow/workflow_report/general_report
2. Filter by "Status" & "Initiator Name"
Expected: Only filtered data should be shown
"""
import common as c

TEST_CASE_ID = "REP-TC092"
ROUTE = "/workflow/workflow_report/general_report"
REPORT_NAME = "Test Report 1"
FILTER_LABELS = ["Status", "Initiator Name"]


def test_filter_custom_report(session: c.ReportSession) -> str:
    session.login_as_role("wf_admin")
    session.open_custom_report(ROUTE, report_name=REPORT_NAME)
    return session.search_or_filter(FILTER_LABELS, report_key="custom_report_filter")


if __name__ == "__main__":
    c.run_report_test(TEST_CASE_ID, ROUTE, test_filter_custom_report, __doc__)