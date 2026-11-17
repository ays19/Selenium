"""
REP-TC012: Export/Print/Copy Core Activity Report
1. Go to https://ecmv6.robo2mation.com/report/activity-report/
2. Click on "Copy", "CSV" or "Print" button
Expected: Selected rows core activity report should be copied, printed or (csv) downloaded respectively
"""
import common as c

TEST_CASE_ID = "REP-TC012"
ROUTE = "/report/activity-report/"
EXPORT_ACTIONS = ["Copy", "CSV", "Excel"]


def test_export_core_activity_report(session: c.ReportSession) -> str:
    session.login_as_role("core_report_manager")
    session.open_report(ROUTE)
    return session.export(EXPORT_ACTIONS)


if __name__ == "__main__":
    c.run_report_test(TEST_CASE_ID, ROUTE, test_export_core_activity_report, __doc__)