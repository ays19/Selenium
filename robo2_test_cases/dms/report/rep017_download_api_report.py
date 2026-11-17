"""
REP-TC017: Download API Report
1. Go to https://ecmv6.robo2mation.com/report/published-api-report/
2. Select 10/20/50/all row
3. Click on "Copy", "CSV" or "Print" button
Expected: Selected rows core activity report should be copied, printed or (csv) downloaded respectively
"""
import common as c

TEST_CASE_ID = "REP-TC017"
ROUTE = "/report/published-api-report/"
PAGE_SIZES = ["100", "500", "1000"]
EXPORT_ACTIONS = ["Copy", "CSV", "Excel"]


def test_download_core_api_report(session: c.ReportSession) -> str:
    session.login_as_role("core_report_manager")
    session.open_report(ROUTE)
    return session.export(EXPORT_ACTIONS, page_sizes=PAGE_SIZES)


if __name__ == "__main__":
    c.run_report_test(TEST_CASE_ID, ROUTE, test_download_core_api_report, __doc__)