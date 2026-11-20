"""
DMS-TC092
Metadata Uniqueness
1. Go to https://ecmv6.robo2mation.com/dms/document/root
2. Double click on a doc-type
3. Click on "More" button
4. Click on "Uniqueness Check"
5. Add multiple field as "unique" & separating them with "AND"
System shouldn't allow to upload/edit document with same value on all of these fields & gave proper error message.
Notes: Only allowed to upload/edit if any of these fields value are unique
"""
from datetime import datetime

import common as c

TEST_CASE_ID = "DMS-TC092"


def unique_and(session: c.DmsSession) -> tuple[bool, str]:
    doc_type, (first, second) = session.categorization.setup_uniqueness_doc_type(operator="and")
    run_id = datetime.now().strftime("%H%M%S")

    ok, message = session.upload.upload_with_values(doc_type, {first: f"AUTO_A{run_id}", second: f"AUTO_B{run_id}"})
    if not ok:
        raise c.SetupError(f"first document did not upload ({message})")

    same_all, msg_all = session.upload.upload_with_values(doc_type, {first: f"AUTO_A{run_id}", second: f"AUTO_B{run_id}"})
    one_new, msg_new = session.upload.upload_with_values(doc_type, {first: f"AUTO_A{run_id}", second: f"AUTO_C{run_id}"})
    ok = (not same_all) and one_new
    return ok, (
        f"Same value in all fields: {'rejected' if not same_all else 'ACCEPTED'} ({msg_all}). "
        f"One field different: {'accepted' if one_new else 'REJECTED'} ({msg_new})"
    )


SCENARIOS = [("Unique fields with AND", unique_and)]


def main() -> None:
    c.run_dms_test(TEST_CASE_ID, SCENARIOS, doc=__doc__)


if __name__ == "__main__":
    main()
