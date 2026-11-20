"""
DMS-TC090
Metadata Uniqueness
1. Go to https://ecmv6.robo2mation.com/dms/document/root
2. Double click on a doc-type
3. Click on "More" button
4. Click on "Uniqueness Check"
5. Add a single field as "unique"
System shouldn't allow to upload/edit document with same value on this field & gave proper error message.
"""
from datetime import datetime

import common as c

TEST_CASE_ID = "DMS-TC090"


def single_field(session: c.DmsSession) -> tuple[bool, str]:
    doc_type, fields = session.categorization.setup_uniqueness_doc_type(operator=None)
    field = fields[0]
    value = datetime.now().strftime("AUTO_U%H%M%S")

    ok, message = session.upload.upload_with_values(doc_type, {field: value})
    if not ok:
        raise c.SetupError(f"first document did not upload ({message})")

    ok, message = session.upload.upload_with_values(doc_type, {field: value})
    return (not ok), f"Second document with the same '{field}' value " + (
        f"was rejected: {message}" if not ok else f"was accepted: {message}"
    )


SCENARIOS = [("Single unique field", single_field)]


def main() -> None:
    c.run_dms_test(TEST_CASE_ID, SCENARIOS, doc=__doc__)


if __name__ == "__main__":
    main()
