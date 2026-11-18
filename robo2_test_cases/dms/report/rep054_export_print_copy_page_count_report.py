"""
REP-TC054: Export/Print/Copy Page Count Report
1. Go to https://ecmv6.robo2mation.com/dms/dms_report/page_counts/
2. Click on "Download" icon
3. Click on Copy, CSV, Print
Expected: Selected rows page count report should be copied, printed or (csv) downloaded respectively
"""
import common as c

TEST_CASE_ID = "REP-TC054"
ROUTE = "/dms/dms_report/page_counts/"
EXPORT_ACTIONS = ["Copy", "CSV", "Excel"]


def test_export_page_count_report(session: c.ReportSession) -> str:
    session.login_as_role("dms_report_manager")
    session.open_report(ROUTE)
    return session.export(EXPORT_ACTIONS, requested_download=True)


if __name__ == "__main__":
    c.run_report_test(TEST_CASE_ID, ROUTE, test_export_page_count_report, __doc__)