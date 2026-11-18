"""
REP-TC043: Document Type (Accessibility) Report
1. Go to https://ecmv6.robo2mation.com/dms/dms_report/document-type-report/
2. Users without "DMS Report Manager" permission
Expected: User should be able to access only their document type records
"""
from selenium.webdriver.common.by import By
import common as c

TEST_CASE_ID = "REP-TC043"
ROUTE = "/dms/dms_report/document-type-report/"


def test_own_document_type_accessibility_report(session: c.ReportSession) -> str:
    session.login_as_role("dms_user")
    session.open_report(ROUTE)
    session.report_page.assert_accessible()

    table = session.report_page.report_table(timeout=10)
    rows = table.find_elements(*session.report_page.TABLE_BODY_ROW_LOCATOR) if table else []
    if not rows:
        raise AssertionError("Expected document type accessibility rows for 'dms_user', but table was empty.")

    own_text = c.expected_value("REPORT_EXPECTED_OWN_TEXT") or "ahsan"
    other_text = c.expected_value("REPORT_EXPECTED_OTHER_TEXT") or "nahif"
    dropdown_text = " ".join(
        el.text for el in session.driver.find_elements(By.CSS_SELECTOR, "select option")
    ).casefold()
    page_text = session.report_page.body_text().casefold()

    if own_text.casefold() not in dropdown_text and own_text.casefold() not in page_text:
        raise AssertionError(f"Expected own user '{own_text}' to be selected on the report.")
    if other_text.casefold() in dropdown_text or other_text.casefold() in page_text:
        raise AssertionError(f"Unexpected other user '{other_text}' was accessible to 'dms_user'.")

    return (
        f"Role 'dms_user': sees own document type accessibility records for '{own_text}' "
        f"({len(rows)} row(s)) and cannot access '{other_text}'."
    )


if __name__ == "__main__":
    c.run_report_test(
        TEST_CASE_ID, ROUTE, test_own_document_type_accessibility_report, __doc__
    )
