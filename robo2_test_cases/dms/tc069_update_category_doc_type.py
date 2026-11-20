"""
DMS-TC069
Update Category/Doc Type
1. Go to https://ecmv6.robo2mation.com/dms/document/root
2. Select a category/doc-type
3. Update category/doc-type name with unique value
4. Click on "Save" button
Category/doc-type should be updated with confirmation message
"""
import os

import common as c

TEST_CASE_ID = "DMS-TC069"


def update_category(session: c.DmsSession) -> tuple[bool, str]:
    category = os.getenv("CATEGORY_TO_UPDATE", "").strip()
    new_name = category + "_UPD"
    if len(new_name) > 50:
        raise c.SetupError(f"'{new_name}' is longer than 50 characters, use a shorter category name")

    ok, message = session.categorization.rename_item(category, new_name)
    if not ok:
        return False, message

    try:
        restored, note = session.categorization.rename_item(new_name, category)
    except Exception as error:
        restored, note = False, str(error)
    back = "restored" if restored else f"NOT restored ({note}), rename '{new_name}' back to '{category}' by hand"
    return True, f"{message} ({category} -> {new_name}). Original name {back}"


SCENARIOS = [("Update category", update_category)]


def main() -> None:
    c.run_dms_test(
        TEST_CASE_ID,
        SCENARIOS,
        doc=__doc__,
        required_env=[("CATEGORY_TO_UPDATE", "(name of an existing top-level category)")],
    )


if __name__ == "__main__":
    main()
