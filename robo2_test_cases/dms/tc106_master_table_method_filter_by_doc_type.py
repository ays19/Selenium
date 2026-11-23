"""
DMS-TC106
Master Table Method (Fetch)
1. Go to https://ecmv6.robo2mation.com/dms/document/settings/master-table-method/
2. Filter fetch method according to the doc-type
Only selected doc-types fetch method should be shown
"""
import os

import common as c

TEST_CASE_ID = "DMS-TC106"


def filter_by_doc_type(session: c.DmsSession) -> tuple[bool, str]:
    doc_type = (os.getenv("MASTER_FILTER_DOC_TYPE") or os.getenv("MTM_DOC_TYPE") or "/Chelsea/").strip()
    name = session.master_table.new_method("single record", doc_type=doc_type)
    return session.master_table.filter_by_doc_type(doc_type, expected_method=name)


SCENARIOS = [("Filter by doc-type", filter_by_doc_type)]


def main() -> None:
    c.run_dms_test(
        TEST_CASE_ID,
        SCENARIOS,
        doc=__doc__,
        required_env=[("MASTER_FILTER_DOC_TYPE", "(a doc-type such as /Chelsea/)")],
    )


if __name__ == "__main__":
    main()
