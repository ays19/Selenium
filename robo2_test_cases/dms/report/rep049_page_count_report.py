"""
REP-TC049: Page Count Report
1. Go to https://ecmv6.robo2mation.com/dms/dms_report/page_counts/
2. Users without "DMS Report Manager" permission
Expected: Users should see their permitted doc type page count report
"""
import common as c

TEST_CASE_ID = "REP-TC049"
ROUTE = "/dms/dms_report/page_counts/"


def test_own_page_count_report(session: c.ReportSession) -> str:
    session.login_as_role("dms_user")
    session.open_report(ROUTE)
    return session.verify_scope("accessible")


if __name__ == "__main__":
    c.run_report_test(TEST_CASE_ID, ROUTE, test_own_page_count_report, __doc__)