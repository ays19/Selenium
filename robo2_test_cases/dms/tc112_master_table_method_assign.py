"""
DMS-TC112
Master Table Method (Fetch)
1. Go to https://ecmv6.robo2mation.com/dms/document/settings/master-table-method/
2. Assign a fetch method where all the metadata's are same
1. Fetch method should be assigned to the selected doc-type with proper confirmation message.
2. For single record: Data will be fetched for the selected doc-type.
3. For multiple record: Data will be set for the selected doc-type.
"""
import os

import common as c

TEST_CASE_ID = "DMS-TC112"


def assign(session: c.DmsSession) -> tuple[bool, str]:
    source_doc_type = (os.getenv("MTM_DOC_TYPE") or "/Chelsea/").strip()
    target_doc_type = os.getenv("MASTER_ASSIGN_DOC_TYPE", "").strip()

    single_name = session.master_table.new_method(
        "single record", doc_type=source_doc_type, populate_mt_field="Age", populate_meta_field="salary"
    )
    multi_name = session.master_table.new_method(
        "multiple record", doc_type=source_doc_type, populate_mt_field="Age", populate_meta_field="month"
    )

    ok_as, msg_as = session.master_table.assign_method(single_name, target_doc_type)
    ok_am, msg_am = session.master_table.assign_method(multi_name, target_doc_type)
    if not (ok_as and ok_am):
        return False, f"Assign failed: single=({ok_as}: {msg_as}), multiple=({ok_am}: {msg_am})"

    s_ok, s_msg = session.master_table.verify_fetch_in_upload(
        session.upload, target_doc_type, "name", "Tonmoy", "salary", "single", "22", expect_present=True
    )
    m_ok, m_msg = session.master_table.verify_fetch_in_upload(
        session.upload, target_doc_type, "name", "Tonmoy", "month", "multiple", "22", expect_present=True
    )
    return (s_ok and m_ok), f"{msg_as}; {msg_am} | {s_msg} | {m_msg}"


SCENARIOS = [("Assign method", assign)]


def main() -> None:
    c.run_dms_test(
        TEST_CASE_ID,
        SCENARIOS,
        doc=__doc__,
        required_env=[("MASTER_ASSIGN_DOC_TYPE", "(a doc-type whose meta-data match MTM_DOC_TYPE, e.g. /Shakti Foundation/)")],
    )


if __name__ == "__main__":
    main()
