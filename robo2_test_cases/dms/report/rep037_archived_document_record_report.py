"""
REP-TC037: Archived Document Record Report
1. Go to https://ecmv6.robo2mation.com/dms/dms_report/archived-document-report/
2. Users without "DMS Report Manager" permission
Expected: User should be able to access all documents of a doc-type in Document Records if assigned as access/owner/LMG group user
"""
import common as c

TEST_CASE_ID = "REP-TC037"
ROUTE = "/dms/dms_report/archived-document-report/"


def test_archived_document_record_report_user_scope(session: c.ReportSession) -> str:
    session.login_as_role("dms_user")
    session.open_report(ROUTE)
    return session.verify_document_type_rows()


if __name__ == "__main__":
    c.run_report_test(
        TEST_CASE_ID, ROUTE, test_archived_document_record_report_user_scope, __doc__
    )