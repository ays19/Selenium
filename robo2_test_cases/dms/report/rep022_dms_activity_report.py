"""
REP-TC022: DMS Activity Report
1. Go to https://ecmv6.robo2mation.com/dms/dms_report/dms_activity/
2. Filter By All Operation, All Users
Expected: Filtered data should be accessible
"""
import common as c

TEST_CASE_ID = "REP-TC022"
ROUTE = "/dms/dms_report/dms_activity/"
FILTER_LABELS = ["All Operation", "All Users"]


def test_filter_dms_activity_report(session: c.ReportSession) -> str:
    session.login_as_role("dms_report_manager")
    session.open_report(ROUTE)
    return session.search_or_filter(
        FILTER_LABELS,
        expected_key="REPORT_EXPECTED_FILTER_TEXT_DMS_ACTIVITY_REPORT",
    )


if __name__ == "__main__":
    c.run_report_test(TEST_CASE_ID, ROUTE, test_filter_dms_activity_report, __doc__)