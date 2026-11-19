"""
REP-TC059: KPI Report
1. Go to https://ecmv6.robo2mation.com/workflow/workflow_report/kpi/
2. Search by "User"
Expected: Only searched data should be shown
"""
import common as c

TEST_CASE_ID = "REP-TC059"
ROUTE = "/workflow/workflow_report/kpi/"
SEARCH_LABELS = ["User"]


def test_search_kpi_report(session: c.ReportSession) -> str:
    session.login_as_role("wf_admin")
    session.open_report(ROUTE)
    return session.search_or_filter(
        SEARCH_LABELS,
        expected_key="REPORT_EXPECTED_FILTER_TEXT_KPI_REPORT",
    )


if __name__ == "__main__":
    c.run_report_test(TEST_CASE_ID, ROUTE, test_search_kpi_report, __doc__)