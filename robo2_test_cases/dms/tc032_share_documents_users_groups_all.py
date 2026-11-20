"""
DMS-TC032
Share Documents (Users)
1. Go to "Pending Documents/Document View" page
2. Select single/multiple users
3. Click on "Share" button
Documents should be shared with selected users.

Share Documents (Groups)
1. Go to "Pending Documents/Document View" page
2. Select single/multiple groups
3. Click on "Share" button
Documents should be shared with selected group users.

Share Documents (All User)
1. Go to "Pending Documents/Document View" page
2. Select all user
3. Click on "Share" button
Documents should be shared with all users.
"""
import common as c

TEST_CASE_ID = "DMS-TC032"


def share_with(kind: str):
    def _scenario(session: c.DmsSession) -> tuple[bool, str]:
        info = session.upload_document("pdf", share=kind)
        found = session.explorer.search_finds(info["name"], tries=3)
        if not found:
            return (
                False,
                f"Uploaded with Share With '{info['shared_with']}', but document '{info['name']}' was not found in search",
            )
        return True, f"Document '{info['name']}' uploaded and shared with '{info['shared_with']}' successfully"

    return _scenario


SCENARIOS = [
    ("Users", share_with("users")),
    ("Groups", share_with("groups")),
    ("All users", share_with("all users")),
]


def main() -> None:
    c.run_dms_test(TEST_CASE_ID, SCENARIOS, doc=__doc__, multi_row=True)


if __name__ == "__main__":
    main()
