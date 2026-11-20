"""
DMS-TC036
Share Documents (Email)
1. Go to "Document View" page
2. Click on "Email" button under "Share Document" section
3. Add participants (any valid mail & share doc person), subject & attachment
4. Click on "Send" button
Selected participants should get share doc mail with attachments & system should give proper confirmation message
"""
import os

import common as c

TEST_CASE_ID = "DMS-TC036"


def share_by_email(session: c.DmsSession) -> tuple[bool, str]:
    email = os.getenv("SHARE_EMAIL", "").strip()
    session.new_document()
    return session.document.share_by_email(email)


SCENARIOS = [("Share by email", share_by_email)]


def main() -> None:
    c.run_dms_test(
        TEST_CASE_ID,
        SCENARIOS,
        doc=__doc__,
        required_env=[("SHARE_EMAIL", "(a valid mail address)")],
    )


if __name__ == "__main__":
    main()
