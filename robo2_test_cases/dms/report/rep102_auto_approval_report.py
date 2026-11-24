"""
REP-TC102: Export Auto Approval Report
1. Go to https://ecmv6.robo2mation.com/workflow/workflow_report/wf_auto_approval/
2. Click on "CSV" or "Excel" button
Expected: Selected reports should be downloaded
"""
import common as c

TEST_CASE_ID = "REP-TC102"
ROUTE = "/workflow/workflow_report/wf_auto_approval/"
EXPORT_ACTIONS = ["CSV", "Excel"]


def test_export_auto_approval_report(session: c.ReportSession) -> str:
    session.login_as_role("wf_admin")
    session.open_report(ROUTE)
    return session.export(EXPORT_ACTIONS, requested_download=True)


if __name__ == "__main__":
    c.run_report_test(TEST_CASE_ID, ROUTE, test_export_auto_approval_report, __doc__)