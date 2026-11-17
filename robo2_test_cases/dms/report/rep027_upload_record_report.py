"""
REP-TC027: Upload Record Report
1. Go to https://ecmv6.robo2mation.com/dms/dms_report/upload_report/
2. Search by "User", "Document Name" or "Source IP"
Expected: Only searched data should be shown
"""
import common as c

TEST_CASE_ID = "REP-TC027"
ROUTE = "/dms/dms_report/upload_report/"
SEARCH_LABELS = ["User", "Source IP"]


def test_search_upload_record_report(session: c.ReportSession) -> str:
    session.login_as_role("dms_report_manager")
    session.open_report(ROUTE)
    return session.search_or_filter(
        SEARCH_LABELS,
        expected_key="REPORT_EXPECTED_FILTER_TEXT_UPLOAD_RECORD_REPORT",
    )


if __name__ == "__main__":
    c.run_report_test(TEST_CASE_ID, ROUTE, test_search_upload_record_report, __doc__)