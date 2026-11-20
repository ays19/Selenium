"""
DMS-TC067
Categorization/Doc-Type Creation
1. Go to https://ecmv6.robo2mation.com/dms/document/root
2. Click on "Add" button
3. Select category/doc-type
4. Give a tree wise unique category/doc-type name
5. Click on "Save" button
Category/doc-type should be created with proper confirmation message
"""
import common as c

TEST_CASE_ID = "DMS-TC067"


def create_doc_type(session: c.DmsSession) -> tuple[bool, str]:
    return session.categorization.create_top_level_doc_type()


SCENARIOS = [("Create doc-type", create_doc_type)]


def main() -> None:
    c.run_dms_test(TEST_CASE_ID, SCENARIOS, doc=__doc__)


if __name__ == "__main__":
    main()
