"""
DMS-TC101
Master Table Method (Fetch)
1. Go to https://ecmv6.robo2mation.com/dms/document/settings/share_document/
2. Click on "Add Method" icon
3. Create a "Multiple Record" master table fetch method
1. Multiple record master table method should be created successfully & system should give proper confirmation message.
2. Multiple records should be set on the dropdown fields of the metadataa on upload documents, edit metadata, advanced search & my documents search
"""
import os

import common as c

TEST_CASE_ID = "DMS-TC101"


def multiple_record(session: c.DmsSession) -> tuple[bool, str]:
    doc_type = (os.getenv("MTM_DOC_TYPE") or "/Chelsea/").strip()
    ok, message, name = session.master_table.create_method(
        "multiple record",
        doc_type=doc_type,
        criteria_mt_field="Name",
        criteria_meta_field="name",
        populate_mt_field="Age",
        populate_meta_field="month",
    )
    if not ok:
        return False, f"{message} ({name})"

    info = session.upload.upload_document("pdf", doc_type=doc_type)
    fetch_ok, fetch_msg = session.master_table.verify_fetch_all_contexts(
        session,
        doc_type=doc_type,
        doc_name=info["name"],
        criteria_field="name",
        criteria_value="Tonmoy",
        populate_field="month",
        output_type="multiple",
        expected_value="22",
        expect_present=True,
    )
    return fetch_ok, f"{message} ({name}). {fetch_msg}"


SCENARIOS = [("Multiple record method", multiple_record)]


def main() -> None:
    c.run_dms_test(TEST_CASE_ID, SCENARIOS, doc=__doc__)


if __name__ == "__main__":
    main()
