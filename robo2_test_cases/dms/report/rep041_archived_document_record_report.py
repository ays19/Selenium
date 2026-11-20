"""
REP-TC041: Archived Document Record Report
1. Go to https://ecmv6.robo2mation.com/dms/dms_report/archived-document-report/
2. Filter By Document Type
Expected: Filtered data should be accessible
"""
import common as c

TEST_CASE_ID = "REP-TC041"
ROUTE = "/dms/dms_report/archived-document-report/"


def test_filter_archived_document_record_report(session: c.ReportSession) -> str:
    session.login_as_role("dms_report_manager")
    session.open_report(ROUTE)
    return session.verify_document_type_rows(verify_text=True)


if __name__ == "__main__":
    c.run_report_test(TEST_CASE_ID, ROUTE, test_filter_archived_document_record_report, __doc__)
