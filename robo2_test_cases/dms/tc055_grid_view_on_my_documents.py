"""
DMS-TC055
Grid View on My Documents
1. Go to https://ecmv6.robo2mation.com/dms/document/explorer/
2. Click on "grid" icon
3. Click on "document" icon
4. Click on "view" icon
1. Document list should be shown in grid view
2. Document should be opened in new tab
3. Document quick view modal should be opened
"""
import os

import common as c

TEST_CASE_ID = "DMS-TC055"


def grid_view(session: c.DmsSession) -> tuple[bool, str]:
    doc_type = os.getenv("EXPLORER_DOC_TYPE", "").strip()
    return session.explorer.test_grid_view(doc_type)


SCENARIOS = [("Grid view", grid_view)]


def main() -> None:
    c.run_dms_test(
        TEST_CASE_ID,
        SCENARIOS,
        doc=__doc__,
        required_env=[("EXPLORER_DOC_TYPE", "(path like /LMG DocType/)")],
    )


if __name__ == "__main__":
    main()
