"""
DMS-TC109
Master Table Method (Fetch)
1. Go to https://ecmv6.robo2mation.com/dms/document/settings/master-table-method/
2. Enable a fetch method
3. Method should be enabled with proper confirmation message.
"""
import common as c

TEST_CASE_ID = "DMS-TC109"


def enable(session: c.DmsSession) -> tuple[bool, str]:
    name = session.master_table.new_method()
    ok, message = session.master_table.set_method_disabled(name, target_disabled=True)
    if not ok:
        raise c.SetupError(f"could not disable the method ({message})")
    ok, message = session.master_table.set_method_disabled(name, target_disabled=False)
    return ok, f"{message} ({name}). Data fetching on the upload page is not checked by the script"


SCENARIOS = [("Enable method", enable)]


def main() -> None:
    c.run_dms_test(TEST_CASE_ID, SCENARIOS, doc=__doc__)


if __name__ == "__main__":
    main()
