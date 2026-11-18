"""
REP-TC029: Upload Record Report
1. Go to https://ecmv6.robo2mation.com/dms/dms_report/upload_report/
2. Filter By All Users
Expected: Filtered data should be accessible
"""
import common as c

TEST_CASE_ID = "REP-TC029"
ROUTE = "/dms/dms_report/upload_report/"
FILTER_LABELS = ["All Users"]


def test_filter_upload_record_report(session: c.ReportSession) -> str:
    session.login_as_role("dms_report_manager")
    session.open_report(ROUTE)
    session.select_document_type()
    return session.search_or_filter(
        FILTER_LABELS,
        expected_key="REPORT_EXPECTED_FILTER_TEXT_UPLOAD_RECORD_REPORT",
    )


if __name__ == "__main__":
    c.run_report_test(TEST_CASE_ID, ROUTE, test_filter_upload_record_report, __doc__)