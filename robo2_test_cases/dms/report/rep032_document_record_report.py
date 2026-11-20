"""
REP-TC032: Document Record Report
1. Go to https://ecmv6.robo2mation.com/dms/dms_report/document-record-report/
2. Users with "DMS Report Manager" permission
Expected: User should be able to access all uploaded documents of all docType
"""
import common as c

TEST_CASE_ID = "REP-TC032"
ROUTE = "/dms/dms_report/document-record-report/"


def test_document_record_report_manager_scope(session: c.ReportSession) -> str:
    session.login_as_role("dms_report_manager")
    session.open_report(ROUTE)
    return session.verify_document_type_rows()


if __name__ == "__main__":
    c.run_report_test(TEST_CASE_ID, ROUTE, test_document_record_report_manager_scope, __doc__)
