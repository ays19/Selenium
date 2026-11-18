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
    doc_type = session.select_document_type()
    session.report_page.assert_accessible()
    table = session.report_page.report_table(timeout=10)
    rows = table.find_elements(*session.report_page.TABLE_BODY_ROW_LOCATOR) if table else []
    if not rows:
        raise AssertionError(
            f"Expected documents for doc-type '{doc_type}' on Document Record Report, but table was empty."
        )
    return (
        f"Role 'dms_report_manager': accessed Document Record Report for doc-type '{doc_type}' "
        f"({len(rows)} row(s) visible)."
    )


if __name__ == "__main__":
    c.run_report_test(TEST_CASE_ID, ROUTE, test_document_record_report_manager_scope, __doc__)
