"""
REP-TC031: Document Record Report
1. Go to https://ecmv6.robo2mation.com/dms/dms_report/document-record-report/
2. Users without "DMS Report Manager" permission
Expected: User should be able to access all documents of a doc-type in Document Records if assigned as access/owner/LMG group user
"""
import common as c

TEST_CASE_ID = "REP-TC031"
ROUTE = "/dms/dms_report/document-record-report/"


def test_document_record_report_user_scope(session: c.ReportSession) -> str:
    session.login_as_role("dms_user")
    session.open_report(ROUTE)
    doc_type = session.select_document_type()
    session.report_page.assert_accessible()
    table = session.report_page.report_table(timeout=10)
    rows = table.find_elements(*session.report_page.TABLE_BODY_ROW_LOCATOR) if table else []
    if not rows:
        raise AssertionError(
            f"Expected documents for doc-type '{doc_type}' on Document Record Report, but table was empty."
        )
    return (
        f"Role 'dms_user': accessed Document Record Report for doc-type '{doc_type}' "
        f"({len(rows)} row(s) visible)."
    )


if __name__ == "__main__":
    c.run_report_test(TEST_CASE_ID, ROUTE, test_document_record_report_user_scope, __doc__)
