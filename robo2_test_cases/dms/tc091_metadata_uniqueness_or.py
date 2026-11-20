"""
DMS-TC091
Metadata Uniqueness
1. Go to https://ecmv6.robo2mation.com/dms/document/root
2. Double click on a doc-type
3. Click on "More" button
4. Click on "Uniqueness Check"
5. Add multiple field as "unique" & separating them with "OR"
System shouldn't allow to upload/edit document with same value on any of these fields & gave proper error message.
Notes: Only allowed to upload/edit if all of these fields value are unique
"""
from datetime import datetime

import common as c

TEST_CASE_ID = "DMS-TC091"


def unique_or(session: c.DmsSession) -> tuple[bool, str]:
    doc_type, (first, second) = session.categorization.setup_uniqueness_doc_type(operator="or")
    run_id = datetime.now().strftime("%H%M%S")

    ok, message = session.upload.upload_with_values(doc_type, {first: f"AUTO_A{run_id}", second: f"AUTO_B{run_id}"})
    if not ok:
        raise c.SetupError(f"first document did not upload ({message})")

    same_one, msg_one = session.upload.upload_with_values(doc_type, {first: f"AUTO_A{run_id}", second: f"AUTO_C{run_id}"})
    all_new, msg_new = session.upload.upload_with_values(doc_type, {first: f"AUTO_D{run_id}", second: f"AUTO_E{run_id}"})
    ok = (not same_one) and all_new
    return ok, (
        f"Same value in one field: {'rejected' if not same_one else 'ACCEPTED'} ({msg_one}). "
        f"All values new: {'accepted' if all_new else 'REJECTED'} ({msg_new})"
    )


SCENARIOS = [("Unique fields with OR", unique_or)]


def main() -> None:
    c.run_dms_test(TEST_CASE_ID, SCENARIOS, doc=__doc__)


if __name__ == "__main__":
    main()
