"""
DMS-TC105
Master Table Method (Fetch)
1. Go to https://ecmv6.robo2mation.com/dms/document/settings/share_document/
2. Delete a master table fetch method
1. Master table method should be deleted & system should give proper confirmation message.
2. Single record won't be fetched & multiple record won't be set for the deleted methods.
"""
import os

import common as c

TEST_CASE_ID = "DMS-TC105"


def delete_method(session: c.DmsSession) -> tuple[bool, str]:
    doc_type = (os.getenv("MTM_DOC_TYPE") or "/Chelsea/").strip()
    single_name = session.master_table.new_method(
        "single record", doc_type=doc_type, populate_mt_field="Age", populate_meta_field="salary"
    )
    multi_name = session.master_table.new_method(
        "multiple record", doc_type=doc_type, populate_mt_field="Age", populate_meta_field="month"
    )

    s_before_ok, s_before_msg = session.master_table.verify_fetch_in_upload(
        session.upload, doc_type, "name", "Tonmoy", "salary", "single", "22", expect_present=True
    )
    m_before_ok, m_before_msg = session.master_table.verify_fetch_in_upload(
        session.upload, doc_type, "name", "Tonmoy", "month", "multiple", "22", expect_present=True
    )
    if not (s_before_ok and m_before_ok):
        raise c.SetupError(f"methods did not fetch before deletion ({s_before_msg}; {m_before_msg})")

    ok_s, msg_s = session.master_table.delete_method(single_name)
    ok_m, msg_m = session.master_table.delete_method(multi_name)
    if not (ok_s and ok_m):
        return False, f"Delete failed: single=({ok_s}: {msg_s}), multiple=({ok_m}: {msg_m})"

    s_after_ok, s_after_msg = session.master_table.verify_fetch_in_upload(
        session.upload, doc_type, "name", "Tonmoy", "salary", "single", "22", expect_present=False
    )
    m_after_ok, m_after_msg = session.master_table.verify_fetch_in_upload(
        session.upload, doc_type, "name", "Tonmoy", "month", "multiple", "22", expect_present=False
    )
    passed = s_after_ok and m_after_ok
    return passed, f"Deleted {single_name} & {multi_name}: {msg_s}; After delete: {s_after_msg} | {m_after_msg}"


SCENARIOS = [("Delete method", delete_method)]


def main() -> None:
    c.run_dms_test(TEST_CASE_ID, SCENARIOS, doc=__doc__)


if __name__ == "__main__":
    main()
