"""
DMS-TC109
Master Table Method (Fetch)
1. Go to https://ecmv6.robo2mation.com/dms/document/settings/master-table-method/
2. Enable a fetch method
1. Method should be enabled with proper confirmation message.
2. For single record: Data will be fetched again.
3. For multiple record: Data will be set again.
"""
import os

import common as c

TEST_CASE_ID = "DMS-TC109"


def enable(session: c.DmsSession) -> tuple[bool, str]:
    doc_type = (os.getenv("MTM_DOC_TYPE") or "/Chelsea/").strip()
    single_name = session.master_table.new_method(
        "single record", doc_type=doc_type, populate_mt_field="Age", populate_meta_field="salary"
    )
    multi_name = session.master_table.new_method(
        "multiple record", doc_type=doc_type, populate_mt_field="Age", populate_meta_field="month"
    )

    ok_ds, msg_ds = session.master_table.set_method_disabled(single_name, target_disabled=True)
    ok_dm, msg_dm = session.master_table.set_method_disabled(multi_name, target_disabled=True)
    if not (ok_ds and ok_dm):
        raise c.SetupError(f"could not disable methods first ({msg_ds}; {msg_dm})")

    ok_es, msg_es = session.master_table.set_method_disabled(single_name, target_disabled=False)
    ok_em, msg_em = session.master_table.set_method_disabled(multi_name, target_disabled=False)
    if not (ok_es and ok_em):
        return False, f"Enable failed: single=({ok_es}: {msg_es}), multiple=({ok_em}: {msg_em})"

    s_on_ok, s_on_msg = session.master_table.verify_fetch_in_upload(
        session.upload, doc_type, "name", "Tonmoy", "salary", "single", "22", expect_present=True
    )
    m_on_ok, m_on_msg = session.master_table.verify_fetch_in_upload(
        session.upload, doc_type, "name", "Tonmoy", "month", "multiple", "22", expect_present=True
    )
    return (s_on_ok and m_on_ok), f"Re-enabled {single_name} & {multi_name}: {msg_es} | {s_on_msg} | {m_on_msg}"


SCENARIOS = [("Enable method", enable)]


def main() -> None:
    c.run_dms_test(TEST_CASE_ID, SCENARIOS, doc=__doc__)


if __name__ == "__main__":
    main()
