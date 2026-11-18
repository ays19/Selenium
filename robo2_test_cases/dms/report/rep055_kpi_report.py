"""
REP-TC055: KPI Report
1. Go to https://ecmv6.robo2mation.com/workflow/workflow_report/kpi/
Expected: User's whom are not assigned to any department/sub-department should see own KPI report
"""
import common as c

TEST_CASE_ID = "REP-TC055"
ROUTE = "/workflow/workflow_report/kpi/"


def test_unassigned_user_own_kpi_report(session: c.ReportSession) -> str:
    session.login_as_role("wf_unassigned_user")
    session.open_report(ROUTE)
    return session.verify_scope("own")


if __name__ == "__main__":
    c.run_report_test(TEST_CASE_ID, ROUTE, test_unassigned_user_own_kpi_report, __doc__)