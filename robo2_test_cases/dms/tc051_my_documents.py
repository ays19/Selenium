"""
DMS-TC051
My Documents
1. Go to https://ecmv6.robo2mation.com/dms/document/explorer/
Only permitted sub category/doc-type should be shown for general user
"""
import os

import common as c

TEST_CASE_ID = "DMS-TC051"


def permitted_only(session: c.DmsSession) -> tuple[bool, str]:
    visible_type = os.getenv("OTHER_USER_VISIBLE_DOC_TYPE", "").strip()
    hidden_type = os.getenv("OTHER_USER_HIDDEN_DOC_TYPE", "").strip()

    names = [n.lower() for n in session.as_other_user(session.explorer.load_explorer_tree_names)]
    sees_visible = visible_type.lower() in names
    sees_hidden = hidden_type.lower() in names
    ok = sees_visible and not sees_hidden
    return ok, (
        f"General user sees '{visible_type}': {'yes' if sees_visible else 'NO'}. "
        f"Sees '{hidden_type}': {'YES' if sees_hidden else 'no'}"
    )


SCENARIOS = [("Permitted doc-types only", permitted_only)]


def main() -> None:
    c.run_dms_test(
        TEST_CASE_ID,
        SCENARIOS,
        doc=__doc__,
        need_other_user=True,
        required_env=[
            ("OTHER_USER_VISIBLE_DOC_TYPE", "(a doc-type the second user can see)"),
            ("OTHER_USER_HIDDEN_DOC_TYPE", "(a doc-type the second user can not see)"),
        ],
    )


if __name__ == "__main__":
    main()
