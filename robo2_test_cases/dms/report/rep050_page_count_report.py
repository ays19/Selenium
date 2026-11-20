"""
REP-TC050: Page Count Report
1. Go to https://ecmv6.robo2mation.com/dms/dms_report/page_counts/
2. Users with "DMS Report Manager" permission
Expected: User should see all doc types page count report with "document type", "documents", "pages" & "full path"
"""
import common as c

TEST_CASE_ID = "REP-TC050"
ROUTE = "/dms/dms_report/page_counts/"
EXPECTED_COLUMNS = ["Document Type", "Documents", "Pages", "Full Path"]


def test_all_page_count_report(session: c.ReportSession) -> str:
    session.login_as_role("dms_report_manager")
    session.open_report(ROUTE)
    scope_msg = session.verify_scope("accessible")
    cols_msg = session.verify_columns(EXPECTED_COLUMNS)
    return f"{scope_msg} {cols_msg}"


if __name__ == "__main__":
    c.run_report_test(TEST_CASE_ID, ROUTE, test_all_page_count_report, __doc__)
