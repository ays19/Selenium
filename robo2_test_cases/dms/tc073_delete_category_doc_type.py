"""
DMS-TC073
Delete Category/Doc Type
1. Go to https://ecmv6.robo2mation.com/dms/document/root
2. Select a category/doc-type that doesn't have any document uploaded
3. Click on delete
Category/doc-type should be deleted with confirmation message
"""
import common as c

TEST_CASE_ID = "DMS-TC073"


def delete_doc_type(session: c.DmsSession) -> tuple[bool, str]:
    name = session.categorization.new_doc_type()
    ok, message = session.categorization.delete_category(name)
    return ok, f"{message} ({name})"


SCENARIOS = [("Delete doc-type", delete_doc_type)]


def main() -> None:
    c.run_dms_test(TEST_CASE_ID, SCENARIOS, doc=__doc__)


if __name__ == "__main__":
    main()
