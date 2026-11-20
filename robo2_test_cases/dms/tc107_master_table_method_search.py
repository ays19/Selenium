"""
DMS-TC107
Master Table Method (Fetch)
1. Go to https://ecmv6.robo2mation.com/dms/document/settings/master-table-method/
2. Search by "method name" & "master table"
Only searched fetch method should be shown
"""
import common as c

TEST_CASE_ID = "DMS-TC107"


def search_method(session: c.DmsSession) -> tuple[bool, str]:
    name = session.master_table.new_method()
    session.master_table.new_method()  # second method so search actually filters
    return session.master_table.search_method(name)


SCENARIOS = [("Search by method name", search_method)]


def main() -> None:
    c.run_dms_test(TEST_CASE_ID, SCENARIOS, doc=__doc__)


if __name__ == "__main__":
    main()
