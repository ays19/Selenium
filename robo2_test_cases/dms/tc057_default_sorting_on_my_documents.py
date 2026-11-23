"""
DMS-TC057
Default Sorting on My Documents
1. Go to https://ecmv6.robo2mation.com/dms/document/explorer/
2. Select a doc-type which has document
1. By default document should be shown as date wise descending
2. Sorting should work for page changes
"""
import os

import common as c

TEST_CASE_ID = "DMS-TC057"


def sorting(session: c.DmsSession) -> tuple[bool, str]:
    doc_type = os.getenv("EXPLORER_DOC_TYPE", "").strip()
    return session.explorer.verify_document_sorting(
        doc_type,
        order_label=None,
        by="date",
        descending=True,
        label_desc="Date descending (default)",
    )


SCENARIOS = [("Date descending (default)", sorting)]


def main() -> None:
    c.run_dms_test(
        TEST_CASE_ID,
        SCENARIOS,
        doc=__doc__,
        required_env=[("EXPLORER_DOC_TYPE", "(path like /LMG DocType/, with more than one page of documents)")],
    )


if __name__ == "__main__":
    main()
