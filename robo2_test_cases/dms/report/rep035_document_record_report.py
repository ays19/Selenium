"""
REP-TC035: Document Record Report
1. Go to https://ecmv6.robo2mation.com/dms/dms_report/document-record-report/
2. Filter By Document Type
Expected: Filtered data should be accessible
"""
import common as c

TEST_CASE_ID = "REP-TC035"
ROUTE = "/dms/dms_report/document-record-report/"


def test_filter_document_record_report(session: c.ReportSession) -> str:
    session.login_as_role("dms_report_manager")
    session.open_report(ROUTE)
    return session.verify_document_type_rows()


if __name__ == "__main__":
    c.run_report_test(TEST_CASE_ID, ROUTE, test_filter_document_record_report, __doc__)
