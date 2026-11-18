"""
REP-TC056: KPI Report
1. Go to https://ecmv6.robo2mation.com/workflow/workflow_report/kpi/
Expected: Admin should see all users KPI report
"""
import common as c

TEST_CASE_ID = "REP-TC056"
ROUTE = "/workflow/workflow_report/kpi/"


def test_admin_all_users_kpi_report(session: c.ReportSession) -> str:
    session.login_as_role("wf_admin")
    session.open_report(ROUTE)
    return session.verify_scope("all")


if __name__ == "__main__":
    c.run_report_test(TEST_CASE_ID, ROUTE, test_admin_all_users_kpi_report, __doc__)