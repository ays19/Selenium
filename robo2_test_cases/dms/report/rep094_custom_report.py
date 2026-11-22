"""
REP-TC094: Download Custom Report (Front End)
1. Go to https://ecmv6.robo2mation.com/workflow/workflow_report/general_report
2. Download custom report from front end
Expected: Report should be directly downloaded
"""
import common as c

TEST_CASE_ID = "REP-TC094"
ROUTE = "/workflow/workflow_report/general_report"
REPORT_NAME = "Default Variable Report"
EXPORT_ACTIONS = ["Copy", "CSV", "Excel"]


def test_download_custom_report_frontend(session: c.ReportSession) -> str:
    session.login_as_role("wf_admin")
    session.open_custom_report(ROUTE, report_name=REPORT_NAME)
    return session.export(EXPORT_ACTIONS, requested_download=False)


if __name__ == "__main__":
    c.run_report_test(TEST_CASE_ID, ROUTE, test_download_custom_report_frontend, __doc__)