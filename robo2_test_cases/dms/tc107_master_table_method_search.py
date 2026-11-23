"""
DMS-TC107
Master Table Method (Fetch)
1. Go to https://ecmv6.robo2mation.com/dms/document/settings/master-table-method/
2. Search by "method name" & "master table"
Only searched fetch method should be shown
"""
import os

import common as c

TEST_CASE_ID = "DMS-TC107"


def search_method(session: c.DmsSession) -> tuple[bool, str]:
    master_table = (os.getenv("MTM_MASTER_TABLE") or "Maverick").strip()
    name = session.master_table.new_method("single record", master_table=master_table)
    session.master_table.new_method("multiple record", master_table=master_table)  # second method so search actually filters

    by_name_ok, by_name_msg = session.master_table.search_method(name, by="method")
    by_table_ok, by_table_msg = session.master_table.search_method(master_table, by="table")
    return (by_name_ok and by_table_ok), f"{by_name_msg} | {by_table_msg}"


SCENARIOS = [("Search by method name & master table", search_method)]


def main() -> None:
    c.run_dms_test(TEST_CASE_ID, SCENARIOS, doc=__doc__)


if __name__ == "__main__":
    main()
