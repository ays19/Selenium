"""
DMS-TC087
Delete Metadata
1. Go to https://ecmv6.robo2mation.com/dms/document/root
2. Double click on a doc-type
3. Select a metadata
4. Click on "Delete" button
Metadata should be deleted with confirmation message
"""
import common as c

TEST_CASE_ID = "DMS-TC087"


def delete_metadata(session: c.DmsSession) -> tuple[bool, str]:
    doc_type = session.categorization.new_doc_type()
    display = session.categorization.new_metadata(doc_type)
    ok, message = session.categorization.delete_metadata(display)
    return ok, f"{message} ('{display}' in {doc_type})"


SCENARIOS = [("Delete metadata", delete_metadata)]


def main() -> None:
    c.run_dms_test(TEST_CASE_ID, SCENARIOS, doc=__doc__)


if __name__ == "__main__":
    main()
