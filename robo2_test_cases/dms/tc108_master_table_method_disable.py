"""
DMS-TC108
Master Table Method (Fetch)
1. Go to https://ecmv6.robo2mation.com/dms/document/settings/master-table-method/
2. Disable a fetch method
1. Method should be disabled with proper confirmation message.
2. For single record: Data won't be fetched.
3. For multiple record: Data won't be set.
"""
import os

import common as c

TEST_CASE_ID = "DMS-TC108"


def disable(session: c.DmsSession) -> tuple[bool, str]:
    doc_type = (os.getenv("MTM_DOC_TYPE") or "/Chelsea/").strip()
    single_name = session.master_table.new_method(
        "single record", doc_type=doc_type, populate_mt_field="Age", populate_meta_field="salary"
    )
    multi_name = session.master_table.new_method(
        "multiple record", doc_type=doc_type, populate_mt_field="Age", populate_meta_field="month"
    )

    ok_s, msg_s = session.master_table.set_method_disabled(single_name, target_disabled=True)
    ok_m, msg_m = session.master_table.set_method_disabled(multi_name, target_disabled=True)
    if not (ok_s and ok_m):
        return False, f"Disable failed: single=({ok_s}: {msg_s}), multiple=({ok_m}: {msg_m})"

    s_off_ok, s_off_msg = session.master_table.verify_fetch_in_upload(
        session.upload, doc_type, "name", "Tonmoy", "salary", "single", "22", expect_present=False
    )
    m_off_ok, m_off_msg = session.master_table.verify_fetch_in_upload(
        session.upload, doc_type, "name", "Tonmoy", "month", "multiple", "22", expect_present=False
    )
    return (s_off_ok and m_off_ok), f"Disabled {single_name} & {multi_name}: {msg_s} | {s_off_msg} | {m_off_msg}"


SCENARIOS = [("Disable method", disable)]


def main() -> None:
    c.run_dms_test(TEST_CASE_ID, SCENARIOS, doc=__doc__)


if __name__ == "__main__":
    main()
