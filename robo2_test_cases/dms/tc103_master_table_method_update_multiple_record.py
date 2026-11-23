"""
DMS-TC103
Master Table Method (Fetch)
1. Go to https://ecmv6.robo2mation.com/dms/document/settings/share_document/
2. Update a "Multiple Record" master table fetch method
1. Multiple record master table method should be updated successfully & system should give proper confirmation message.
2. Multiple records should be set on the dropdown fields of the metadataa on upload documents, edit metadata, advanced search & my documents search
"""
import os

import common as c

TEST_CASE_ID = "DMS-TC103"


def update(session: c.DmsSession) -> tuple[bool, str]:
    doc_type = (os.getenv("MTM_DOC_TYPE") or "/Chelsea/").strip()
    name = session.master_table.new_method(
        "multiple record",
        doc_type=doc_type,
        criteria_mt_field="Name",
        criteria_meta_field="name",
        populate_mt_field="Age",
        populate_meta_field="month",
    )
    new_name = name + "_UPD"
    ok, message = session.master_table.update_method(
        name,
        new_name,
        populate_mt_field="Name",
        populate_meta_field="month",
    )
    if not ok:
        return False, f"{message} ({name} -> {new_name})"

    info = session.upload.upload_document("pdf", doc_type=doc_type)
    fetch_ok, fetch_msg = session.master_table.verify_fetch_all_contexts(
        session,
        doc_type=doc_type,
        doc_name=info["name"],
        criteria_field="name",
        criteria_value="Tonmoy",
        populate_field="month",
        output_type="multiple",
        expected_value="Tonmoy",
        expect_present=True,
    )
    return fetch_ok, f"{message} ({name} -> {new_name}). {fetch_msg}"


SCENARIOS = [("Update multiple record method", update)]


def main() -> None:
    c.run_dms_test(TEST_CASE_ID, SCENARIOS, doc=__doc__)


if __name__ == "__main__":
    main()
