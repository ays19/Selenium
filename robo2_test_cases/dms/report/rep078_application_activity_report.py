"""
REP-TC078: Download Application Activity Report (Front End)
1. Go to https://ecmv6.robo2mation.com/workflow/workflow_report/overall_monitor/
2. Download Application Activity Report from front end
Expected: Report should be directly downloaded
"""
import common as c

TEST_CASE_ID = "REP-TC078"
ROUTE = "/workflow/workflow_report/overall_monitor/"
EXPORT_ACTIONS = ["Copy", "CSV", "Excel"]


def test_download_application_activity_frontend(session: c.ReportSession) -> str:
    session.login_as_role("wf_admin")
    session.open_report(ROUTE)
    return session.export(EXPORT_ACTIONS, requested_download=False)


if __name__ == "__main__":
    c.run_report_test(
        TEST_CASE_ID, ROUTE, test_download_application_activity_frontend, __doc__
    )