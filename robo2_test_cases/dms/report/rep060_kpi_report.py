"""
REP-TC060: KPI Report
1. Go to https://ecmv6.robo2mation.com/workflow/workflow_report/kpi/
2. Filter by "User" & "Department"
Expected: Only filtered data should be shown
"""
import common as c

TEST_CASE_ID = "REP-TC060"
ROUTE = "/workflow/workflow_report/kpi/"
FILTER_LABELS = ["User", "Department"]


def test_filter_kpi_report(session: c.ReportSession) -> str:
    session.login_as_role("wf_admin")
    session.open_report(ROUTE)
    return session.search_or_filter(FILTER_LABELS, report_key="kpi_filter")


if __name__ == "__main__":
    c.run_report_test(TEST_CASE_ID, ROUTE, test_filter_kpi_report, __doc__)
