"""
Module for providing a service for managing catalogue categories using the `CatalogueCategoryRepo` repository.
"""

import logging
from typing import Annotated, Any, List, Optional

from fastapi import Depends

from inventory_management_system_api.core.custom_object_id import CustomObjectId
from inventory_management_system_api.core.exceptions import (
    ChildElementsExistError,
    LeafCatalogueCategoryError,
    MissingRecordError,
)
from inventory_management_system_api.models.catalogue_category import CatalogueCategoryIn, CatalogueCategoryOut
from inventory_management_system_api.repositories.catalogue_category import CatalogueCategoryRepo
from inventory_management_system_api.repositories.unit import UnitRepo
from inventory_management_system_api.schemas.breadcrumbs import BreadcrumbsGetSchema
from inventory_management_system_api.schemas.catalogue_category import (
    CATALOGUE_CATEGORY_WITH_CHILD_NON_EDITABLE_FIELDS,
    CatalogueCategoryPatchSchema,
    CatalogueCategoryPostPropertySchema,
    CatalogueCategoryPostSchema,
)
from inventory_management_system_api.services import utils

logger = logging.getLogger()


class CatalogueCategoryService:
    """
    Service for managing catalogue categories.
    """

    def __init__(
        self,
        catalogue_category_repository: Annotated[CatalogueCategoryRepo, Depends(CatalogueCategoryRepo)],
        unit_repository: Annotated[UnitRepo, Depends(UnitRepo)],
    ) -> None:
        """
        Initialise the `CatalogueCategoryService` with a `CatalogueCategoryRepo` and `UnitRepo` repository.

        :param catalogue_category_repository: The `CatalogueCategoryRepo` repository to use.
        :param unit_repository: The `UnitRepo` repository to use.
        """
        self._catalogue_category_repository = catalogue_category_repository
        self._unit_repository = unit_repository

    def create(self, catalogue_category: CatalogueCategoryPostSchema) -> CatalogueCategoryOut:
        """
        Create a new catalogue category.

        The method checks if the parent catalogue is a leaf catalogue category and raises a
        `LeafCatalogueCategoryError` if it is.

        :param catalogue_category: The catalogue category to be created.
        :return: The created catalogue category.
        :raises LeafCatalogueCategoryError: If the parent catalogue category is a leaf catalogue category.
        """
        parent_id = catalogue_category.parent_id
        parent_catalogue_category = self.get(parent_id) if parent_id else None

        if parent_catalogue_category and parent_catalogue_category.is_leaf:
            raise LeafCatalogueCategoryError("Cannot add catalogue category to a leaf parent catalogue category")

        properties = []
        if catalogue_category.properties:
            utils.check_duplicate_property_names(catalogue_category.properties)

            properties = self._add_property_unit_values(catalogue_category.properties)

        code = utils.generate_code(catalogue_category.name, "catalogue category")

        return self._catalogue_category_repository.create(
            CatalogueCategoryIn(
                **{
                    **catalogue_category.model_dump(),
                    "properties": properties,
                    "code": code,
                }
            )
        )

    def get(self, catalogue_category_id: str) -> Optional[CatalogueCategoryOut]:
        """
        Retrieve a catalogue category by its ID.

        :param catalogue_category_id: The ID of the catalogue category to retrieve.
        :return: The retrieved catalogue category, or `None` if not found.
        """
        return self._catalogue_category_repository.get(catalogue_category_id)

    def get_breadcrumbs(self, catalogue_category_id: str) -> BreadcrumbsGetSchema:
        """
        Retrieve the breadcrumbs for a specific catalogue category

        :param catalogue_category_id: ID of the system to retrieve breadcrumbs for
        :return: Breadcrumbs
        """
        return self._catalogue_category_repository.get_breadcrumbs(catalogue_category_id)

    def list(self, parent_id: Optional[str]) -> List[CatalogueCategoryOut]:
        """
        Retrieve catalogue categories based on the provided filters.

        :param parent_id: The `parent_id` to filter catalogue categories by.
        :return: A list of catalogue categories, or an empty list if no catalogue categories are retrieved.
        """
        return self._catalogue_category_repository.list(parent_id)

    def update(
        self, catalogue_category_id: str, catalogue_category: CatalogueCategoryPatchSchema
    ) -> CatalogueCategoryOut:
        """
        Update a catalogue category by its ID.

        The method checks if a catalogue category with such ID exists and raises a `MissingRecordError` if it doesn't
        exist. If a category is attempted to be moved to a leaf parent catalogue category then it checks if the parent
        is a leaf catalogue category and raises a `LeafCatalogueCategoryError` if it is.

        :param catalogue_category_id: The ID of the catalogue category to update.
        :param catalogue_category: The catalogue category containing the fields that need to be updated.
        :return: The updated catalogue category.
        :raises ChildElementsExistError: If the catalogue category has child elements and attempting to update
                                    either any of the disallowed properties (is_leaf or properties)
        :raises MissingRecordError: If the catalogue category doesn't exist.
        :raises LeafCatalogueCategoryError: If the parent catalogue category to which the catalogue category is
                                            attempted to be moved is a leaf catalogue category.
        """
        update_data = catalogue_category.model_dump(exclude_unset=True)

        stored_catalogue_category = self.get(catalogue_category_id)
        if not stored_catalogue_category:
            raise MissingRecordError(f"No catalogue category found with ID: {catalogue_category_id}")

        # If any of these, need to ensure the category has no child elements
        if any(key in update_data for key in CATALOGUE_CATEGORY_WITH_CHILD_NON_EDITABLE_FIELDS):
            if self._catalogue_category_repository.has_child_elements(CustomObjectId(catalogue_category_id)):
                raise ChildElementsExistError(
                    f"Catalogue category with ID {str(catalogue_category_id)} has child elements and cannot be updated"
                )

        if "name" in update_data and catalogue_category.name != stored_catalogue_category.name:
            update_data["code"] = utils.generate_code(catalogue_category.name, "catalogue category")

        if "parent_id" in update_data and catalogue_category.parent_id != stored_catalogue_category.parent_id:
            parent_catalogue_category = self.get(catalogue_category.parent_id) if catalogue_category.parent_id else None

            if parent_catalogue_category and parent_catalogue_category.is_leaf:
                raise LeafCatalogueCategoryError("Cannot add catalogue category to a leaf parent catalogue category")

        if catalogue_category.properties:
            utils.check_duplicate_property_names(catalogue_category.properties)

            properties = self._add_property_unit_values(catalogue_category.properties)
            update_data["properties"] = properties

        return self._catalogue_category_repository.update(
            catalogue_category_id, CatalogueCategoryIn(**{**stored_catalogue_category.model_dump(), **update_data})
        )

    def delete(self, catalogue_category_id: str) -> None:
        """
        Delete a catalogue category by its ID.

        :param catalogue_category_id: The ID of the catalogue category to delete.
        """
        return self._catalogue_category_repository.delete(catalogue_category_id)

    def _add_property_unit_values(
        self,
        properties: List[CatalogueCategoryPostPropertySchema],
    ) -> List[dict[str, Any]]:
        """
        Adds the unit values to the properties based on the provided unit IDs.

        :param properties: List of properties to which unit values will be added.
        :return: List of properties with unit values added.
        :raises MissingRecordError: If a unit with the specified ID is not found.
        """
        logger.info("Adding unit values to the properties")
        properties_with_units = []
        for prop in properties:
            if prop.unit_id is not None:
                unit = self._unit_repository.get(prop.unit_id)
                if not unit:
                    raise MissingRecordError(f"No unit found with ID: {prop.unit_id}")

                # Copy unit value to property
                properties_with_units.append({**prop.model_dump(), "unit": unit.value})
            else:
                properties_with_units.append({**prop.model_dump(), "unit": None})
        return properties_with_units
