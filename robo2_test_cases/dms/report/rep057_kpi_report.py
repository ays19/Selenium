"""
REP-TC057: KPI Report
1. Go to https://ecmv6.robo2mation.com/workflow/workflow_report/kpi/
Expected: Manager or HOD of a department/sub-department users should see their own departments or below sub departments KPI report
"""
import common as c

TEST_CASE_ID = "REP-TC057"
ROUTE = "/workflow/workflow_report/kpi/"


def test_manager_department_kpi_report(session: c.ReportSession) -> str:
    session.login_as_role("wf_manager")
    session.open_report(ROUTE)
    return session.verify_scope("all")


if __name__ == "__main__":
    c.run_report_test(TEST_CASE_ID, ROUTE, test_manager_department_kpi_report, __doc__)