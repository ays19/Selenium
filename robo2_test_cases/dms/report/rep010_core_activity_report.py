"""
REP-TC010: Core Activity Report
1. Go to https://ecmv6.robo2mation.com/report/activity-report/
2. Select a date range
Expected: Only selected dates data should be shown
"""
import common as c

TEST_CASE_ID = "REP-TC010"
ROUTE = "/report/activity-report/"


def test_date_range_core_activity_report(session: c.ReportSession) -> str:
    session.login_as_role("core_report_manager")
    session.open_report(ROUTE)
    return session.filter_by_date(
        expected_key="REPORT_EXPECTED_DATE_TEXT_CORE_ACTIVITY_REPORT"
    )


if __name__ == "__main__":
    c.run_report_test(TEST_CASE_ID, ROUTE, test_date_range_core_activity_report, __doc__)