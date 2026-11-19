"""
REP-TC062: Export KPI Report
1. Go to https://ecmv6.robo2mation.com/workflow/workflow_report/kpi/
2. Click on "Excel or CSV" button while data is less than 100
Expected: 1. Selected users KPI report should be downloaded directly
"""
import common as c

TEST_CASE_ID = "REP-TC062"
ROUTE = "/workflow/workflow_report/kpi/"
EXPORT_ACTIONS = ["CSV", "Excel"]


def test_export_small_kpi_report(session: c.ReportSession) -> str:
    session.login_as_role("wf_admin")
    session.open_report(ROUTE)
    return session.export(EXPORT_ACTIONS, requested_download=False)


if __name__ == "__main__":
    c.run_report_test(TEST_CASE_ID, ROUTE, test_export_small_kpi_report, __doc__)