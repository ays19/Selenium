"""
REP-TC058: KPI Report
1. Go to https://ecmv6.robo2mation.com/workflow/workflow_report/kpi/
Expected: General users (assigned in any department/sub-department) should see their own KPI report
"""
import common as c

TEST_CASE_ID = "REP-TC058"
ROUTE = "/workflow/workflow_report/kpi/"


def test_assigned_user_own_kpi_report(session: c.ReportSession) -> str:
    session.login_as_role("wf_user")
    session.open_report(ROUTE)
    return session.verify_scope("own")


if __name__ == "__main__":
    c.run_report_test(TEST_CASE_ID, ROUTE, test_assigned_user_own_kpi_report, __doc__)