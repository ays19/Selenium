"""
REP-TC051: Page Count Report
1. Go to https://ecmv6.robo2mation.com/dms/dms_report/page_counts/
2. Search by Document Type
Expected: Search by Document Type should display related data
"""
import common as c

TEST_CASE_ID = "REP-TC051"
ROUTE = "/dms/dms_report/page_counts/"
SEARCH_LABELS = ["Document Type"]


def test_search_page_count_report(session: c.ReportSession) -> str:
    session.login_as_role("dms_report_manager")
    session.open_report(ROUTE)
    return session.search_or_filter(
        SEARCH_LABELS,
        expected_key="REPORT_EXPECTED_FILTER_TEXT_PAGE_COUNT_REPORT",
    )


if __name__ == "__main__":
    c.run_report_test(TEST_CASE_ID, ROUTE, test_search_page_count_report, __doc__)