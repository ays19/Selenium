"""
DMS-TC110
Master Table Method (Fetch)
1. Go to https://ecmv6.robo2mation.com/dms/document/settings/master-table-method/
2. Clone a fetch method
3. Method should be cloned with proper confirmation message.
"""
import common as c

TEST_CASE_ID = "DMS-TC110"


def clone(session: c.DmsSession) -> tuple[bool, str]:
    name = session.master_table.new_method()
    ok, message = session.master_table.clone_method(name)
    return ok, f"{message} ({name})"


SCENARIOS = [("Clone method", clone)]


def main() -> None:
    c.run_dms_test(TEST_CASE_ID, SCENARIOS, doc=__doc__)


if __name__ == "__main__":
    main()
