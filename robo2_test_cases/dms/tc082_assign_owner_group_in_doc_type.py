"""
DMS-TC082
Assign Owner Group in Doc-Type
1. Go to https://ecmv6.robo2mation.com/dms/document/root
2. Select a doc-type
3. Click on "Assign Group" button
4. Select one or  multiple groups in "Owner Groups" field
5. Click on "Save" button
1. Selected groups (members) should be assigned as owners in document type with confirmation message
2. Owner group member will get the access of "DMS Owner" roles assigned permission to the selected document type
"""
import common as c

TEST_CASE_ID = "DMS-TC082"


def assign(session: c.DmsSession) -> tuple[bool, str]:
    name = session.categorization.new_doc_type()
    return session.categorization.assign_group(name, kind="owner")


SCENARIOS = [("Assign owner group", assign)]


def main() -> None:
    c.run_dms_test(TEST_CASE_ID, SCENARIOS, doc=__doc__)


if __name__ == "__main__":
    main()
