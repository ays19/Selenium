"""
DMS-TC110
Master Table Method (Fetch)
1. Go to https://ecmv6.robo2mation.com/dms/document/settings/master-table-method/
2. Clone a fetch method
1. Method should be cloned with proper confirmation message.
2. For single record: Data will be fetched.
3. For multiple record: Data will be set.
"""
import os

import common as c

TEST_CASE_ID = "DMS-TC110"


def clone(session: c.DmsSession) -> tuple[bool, str]:
    doc_type = (os.getenv("MTM_DOC_TYPE") or "/Chelsea/").strip()
    single_name = session.master_table.new_method(
        "single record", doc_type=doc_type, populate_mt_field="Age", populate_meta_field="salary"
    )
    ok_cs, msg_cs, clone_s = session.master_table.clone_method(single_name)
    orig_s_id, _ = session.master_table._last_clone_pair
    if not ok_cs:
        return False, f"Clone single failed: {msg_cs}"

    multi_name = session.master_table.new_method(
        "multiple record", doc_type=doc_type, populate_mt_field="Age", populate_meta_field="month"
    )
    ok_cm, msg_cm, clone_m = session.master_table.clone_method(multi_name)
    orig_m_id, _ = session.master_table._last_clone_pair
    if not ok_cm:
        return False, f"Clone multiple failed: {msg_cm}"

    # Disable originals by ID so runtime fetch proves the cloned methods themselves work
    if orig_s_id:
        ok_ds, msg_ds = session.master_table.set_method_disabled(single_name, target_disabled=True, mtm_id=orig_s_id)
        if not ok_ds:
            raise c.SetupError(f"could not disable original single method {orig_s_id} ({msg_ds})")
    if orig_m_id:
        ok_dm, msg_dm = session.master_table.set_method_disabled(multi_name, target_disabled=True, mtm_id=orig_m_id)
        if not ok_dm:
            raise c.SetupError(f"could not disable original multiple method {orig_m_id} ({msg_dm})")

    s_ok, s_msg = session.master_table.verify_fetch_in_upload(
        session.upload, doc_type, "name", "Tonmoy", "salary", "single", "22", expect_present=True
    )
    m_ok, m_msg = session.master_table.verify_fetch_in_upload(
        session.upload, doc_type, "name", "Tonmoy", "month", "multiple", "22", expect_present=True
    )
    return (s_ok and m_ok), f"{msg_cs} ({clone_s}); {msg_cm} ({clone_m}) | {s_msg} | {m_msg}"


SCENARIOS = [("Clone method", clone)]


def main() -> None:
    c.run_dms_test(TEST_CASE_ID, SCENARIOS, doc=__doc__)


if __name__ == "__main__":
    main()
