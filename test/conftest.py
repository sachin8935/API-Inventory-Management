"""
Module for providing pytest testing configuration.
"""

from typing import Optional

from bson import ObjectId

VALID_ACCESS_TOKEN = (
    "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZSI6InVzZXJuYW1lIiwiZXhwIjoyNTM0MDIzMDA3OTl9.bagU2Wix8wKzydVU_L3Z"
    "ZuuMAxGxV4OTuZq_kS2Fuwm839_8UZOkICnPTkkpvsm1je0AWJaIXLGgwEa5zUjpG6lTrMMmzR9Zi63F0NXpJqQqoOZpTBMYBaggsXqFkdsv-yAKUZ"
    "8MfjCEyk3UZ4PXZmEcUZcLhKcXZr4kYJPjio2e5WOGpdjK6q7s-iHGs9DQFT_IoCnw9CkyOKwYdgpB35hIGHkNjiwVSHpyKbFQvzJmIv5XCTSRYqq0"
    "1fldh-QYuZqZeuaFidKbLRH610o2-1IfPMUr-yPtj5PZ-AaX-XTLkuMqdVMCk0_jeW9Os2BPtyUDkpcu1fvW3_S6_dK3nQ"
)

VALID_ACCESS_TOKEN_MISSING_USERNAME = (
    "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjI1MzQwMjMwMDc5OX0.h4Hv_sq4-ika1rpuRx7k3pp0cF_BZ65WVSbIHS7oh9SjPpGHt"
    "GhVHU1IJXzFtyA9TH-68JpAZ24Dm6bXbH6VJKoc7RCbmJXm44ufN32ga7jDqXH340oKvi_wdhEHaCf2HXjzsHHD7_D6XIcxU71v2W5_j8Vuwpr3SdX"
    "6ea_yLIaCDWynN6FomPtUepQAOg3c7DdKohbJD8WhKIDV8UKuLtFdRBfN4HEK5nNs0JroROPhcYM9L_JIQZpdI0c83fDFuXQC-cAygzrSnGJ6O4DyS"
    "cNL3VBNSmNTBtqYOs1szvkpvF9rICPgbEEJnbS6g5kmGld3eioeuDJIxeQglSbxog"
)

EXPIRED_ACCESS_TOKEN = (
    "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZSI6InVzZXJuYW1lIiwiZXhwIjotNjIxMzU1OTY4MDB9.G_cfC8PNYE5yERyyQNRk"
    "9mTmDusU_rEPgm7feo2lWQF6QMNnf8PUN-61FfMNRVE0QDSvAmIMMNEOa8ma0JHZARafgnYJfn1_FSJSoRxC740GpG8EFSWrpM-dQXnoD263V9FlK-"
    "On6IbhF-4Rh9MdoxNyZk2Lj7NvCzJ7gbgbgYM5-sJXLxB-I5LfMfuYM3fx2cRixZFA153l46tFzcMVBrAiBxl_LdyxTIOPfHF0UGlaW2UtFi02gyBU"
    "4E4wTOqPc4t_CSi1oBSbY7h9O63i8IU99YsOCdvZ7AD3ePxyM1xJR7CFHycg9Z_IDouYnJmXpTpbFMMl7SjME3cVMfMrAQ"
)

INVALID_ACCESS_TOKEN = VALID_ACCESS_TOKEN + "1"


def add_ids_to_properties(properties_with_ids: Optional[list], properties_without_ids: list):
    """
    A tests method for adding the IDs from the properties in `properties_with_ids` as the IDs to the properties in
    `properties_without_ids` based on matching names. Unique IDs are generated for each property if no
    `properties_with_ids` are provided. Additionally, unique IDs are generated for each unit if the unit value
    is not None.

    :param properties_with_ids: The list of properties with IDs. These are typically the catalogue category properties.
    :param properties_without_ids: The list of properties without IDs. These can be catalogue category, catalogue item
                                   or item properties.
    :return: The list of properties with the added IDs.
    """
    properties = []
    for property_without_id in properties_without_ids:
        prop_id = None
        unit_id = None

        if properties_with_ids:
            # Match up property and unit IDs
            for property_with_id in properties_with_ids:
                if property_with_id["name"] == property_without_id["name"]:
                    prop_id = property_with_id["id"]

                if property_with_id.get("unit") == property_without_id.get("unit"):
                    unit_id = property_with_id["unit_id"]
        else:
            # Generate a new property id and lookup the unit id from the units list
            prop_id = str(ObjectId())

            if property_without_id.get("unit") is not None:
                if property_without_id.get("unit_id") is None:
                    unit_id = str(ObjectId())
                else:
                    unit_id = property_without_id["unit_id"]

        properties.append({**property_without_id, "id": prop_id, "unit_id": unit_id})

    return properties
