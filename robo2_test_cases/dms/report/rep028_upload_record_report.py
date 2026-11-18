"""
REP-TC028: Upload Record Report
1. Go to https://ecmv6.robo2mation.com/dms/dms_report/upload_report/
2. Select a date range
Expected: Only selected dates data should be shown
"""
import common as c

TEST_CASE_ID = "REP-TC028"
ROUTE = "/dms/dms_report/upload_report/"


def test_date_range_upload_record_report(session: c.ReportSession) -> str:
    session.login_as_role("dms_report_manager")
    session.open_report(ROUTE)
    session.select_document_type()
    return session.filter_by_date(
        expected_key="REPORT_EXPECTED_DATE_TEXT_UPLOAD_RECORD_REPORT"
    )


if __name__ == "__main__":
    c.run_report_test(TEST_CASE_ID, ROUTE, test_date_range_upload_record_report, __doc__)