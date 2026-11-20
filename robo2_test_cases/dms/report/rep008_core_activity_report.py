"""
REP-TC008: Core Activity Report
1. Go to https://ecmv6.robo2mation.com/report/activity-report/
Expected: Should show all core activity report here with proper message
"""
import common as c

TEST_CASE_ID = "REP-TC008"
ROUTE = "/report/activity-report/"


def test_open_core_activity_report(session: c.ReportSession) -> str:
    session.login_as_role("core_report_manager")
    session.open_report(ROUTE)
    return session.verify_has_rows("Core Activity Report")


if __name__ == "__main__":
    c.run_report_test(TEST_CASE_ID, ROUTE, test_open_core_activity_report, __doc__)
