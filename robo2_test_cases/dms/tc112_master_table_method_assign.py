"""
DMS-TC112
Master Table Method (Fetch)
1. Go to https://ecmv6.robo2mation.com/dms/document/settings/master-table-method/
2. Assign a fetch method where all the metadata's are same
3. Fetch method should be assigned to the selected doc-type with proper confirmation message.
"""
import os

import common as c

TEST_CASE_ID = "DMS-TC112"


def assign(session: c.DmsSession) -> tuple[bool, str]:
    doc_type = os.getenv("MASTER_ASSIGN_DOC_TYPE", "").strip()
    name = session.master_table.new_method()
    return session.master_table.assign_method(name, doc_type)


SCENARIOS = [("Assign method", assign)]


def main() -> None:
    c.run_dms_test(
        TEST_CASE_ID,
        SCENARIOS,
        doc=__doc__,
        required_env=[("MASTER_ASSIGN_DOC_TYPE", "(a doc-type whose meta-data match the method)")],
    )


if __name__ == "__main__":
    main()
