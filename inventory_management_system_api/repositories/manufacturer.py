"""
Module for providing a repository for managing manufacturers in a MongoDB database.
"""

import logging
from typing import List, Optional

from pymongo.client_session import ClientSession
from pymongo.collection import Collection

from inventory_management_system_api.core.custom_object_id import CustomObjectId
from inventory_management_system_api.core.database import DatabaseDep
from inventory_management_system_api.core.exceptions import (
    DuplicateRecordError,
    MissingRecordError,
    PartOfCatalogueItemError,
)
from inventory_management_system_api.models.manufacturer import ManufacturerIn, ManufacturerOut

logger = logging.getLogger()


class ManufacturerRepo:
    """Repository for managing manufacturers in a MongoDb database."""

    def __init__(self, database: DatabaseDep) -> None:
        """
        Initialise the `ManufacturerRepo` with a MongoDB database instance.

        :param database: The database to use.
        """
        self._database = database
        self._manufacturers_collection: Collection = self._database.manufacturers
        self._catalogue_items_collection: Collection = self._database.catalogue_items

    def create(self, manufacturer: ManufacturerIn, session: ClientSession = None) -> ManufacturerOut:
        """
        Create a new manufacturer in a MongoDB database.

        :param manufacturer: The manufacturer to be created.
        :param session: PyMongo ClientSession to use for database operations.
        :raises DuplicateRecordError: If a duplicate manufacturer is found.
        :return: The created manufacturer.
        """
        if self._is_duplicate_manufacturer(manufacturer.code, session=session):
            raise DuplicateRecordError("Duplicate manufacturer found")

        logger.info("Inserting the new manufacturer into database")

        result = self._manufacturers_collection.insert_one(manufacturer.model_dump(), session=session)
        manufacturer = self.get(str(result.inserted_id), session=session)

        return manufacturer

    def get(self, manufacturer_id: str, session: ClientSession = None) -> Optional[ManufacturerOut]:
        """
        Retrieve a manufacturer by its ID from a MondoDB database.

        :param manufacturer_id: The ID of the manufacturer to retrieve.
        :param session: PyMongo ClientSession to use for database operations.
        :return: The retrieved manufacturer, or `None` if not found.
        """
        manufacturer_id = CustomObjectId(manufacturer_id)
        logger.info("Retrieving manufacturer with ID: %s from database", manufacturer_id)
        manufacturer = self._manufacturers_collection.find_one({"_id": manufacturer_id}, session=session)
        if manufacturer:
            return ManufacturerOut(**manufacturer)
        return None

    def list(self, session: ClientSession = None) -> List[ManufacturerOut]:
        """
        Retrieve all manufacturers from a MongoDB database.

        :param session: PyMongo ClientSession to use for database operations.
        :return: List of manufacturers, or empty list if no manufacturers.
        """
        logger.info("Getting all manufacturers from the database")
        manufacturers = self._manufacturers_collection.find(session=session)
        return [ManufacturerOut(**manufacturer) for manufacturer in manufacturers]

    def update(
        self, manufacturer_id: str, manufacturer: ManufacturerIn, session: ClientSession = None
    ) -> ManufacturerOut:
        """
        Update manufacturer by its ID in a MongoDB database.

        :param manufacturer_id: The ID of the manufacturer to update.
        :param manufacturer: The manufacturer containing the update data.
        :param session: PyMongo ClientSession to use for database operations.
        :raises DuplicateRecordError: If a duplicate manufacturer is found.
        :return: The updated manufacturer.
        """
        manufacturer_id = CustomObjectId(manufacturer_id)

        stored_manufacturer = self.get(str(manufacturer_id), session=session)
        if stored_manufacturer.name != manufacturer.name:
            if self._is_duplicate_manufacturer(manufacturer.code, manufacturer_id, session=session):
                raise DuplicateRecordError("Duplicate manufacturer found")

        logger.info("Updating manufacturer with ID: %s", manufacturer_id)
        self._manufacturers_collection.update_one(
            {"_id": manufacturer_id}, {"$set": manufacturer.model_dump()}, session=session
        )

        manufacturer = self.get(str(manufacturer_id), session=session)
        return manufacturer

    def delete(self, manufacturer_id: str, session: ClientSession = None) -> None:
        """
        Delete a manufacturer by its ID from a MongoDB database.

        The method checks if the manufacturer is part of a catalogue item, and raises a `PartOfCatalogueItemError` if it
        is.

        :param manufacturer_id: The ID of the manufacturer to delete.
        :param session: PyMongo ClientSession to use for database operations.
        :raises PartOfCatalogueItemError: If the manufacturer is part of a catalogue item.
        :raises MissingRecordError: If the manufacturer doesn't exist.
        """
        manufacturer_id = CustomObjectId(manufacturer_id)
        if self._is_manufacturer_in_catalogue_item(str(manufacturer_id), session=session):
            raise PartOfCatalogueItemError(f"Manufacturer with ID '{str(manufacturer_id)}' is part of a catalogue item")

        logger.info("Deleting manufacturer with ID: %s from the database", manufacturer_id)
        result = self._manufacturers_collection.delete_one({"_id": manufacturer_id}, session=session)
        if result.deleted_count == 0:
            raise MissingRecordError(f"No manufacturer found with ID: {str(manufacturer_id)}")

    def _is_duplicate_manufacturer(
        self, code: str, manufacturer_id: CustomObjectId = None, session: ClientSession = None
    ) -> bool:
        """
        Check if a manufacturer with the same code already exists.

        :param code: The code of the manufacturer to check for duplicates.
        :param manufacturer_id: The ID of the manufacturer to check if the duplicate manufacturer found is itself.
        :param session: PyMongo ClientSession to use for database operations.
        :return: `True` if a duplicate manufacturer is found, `False` otherwise.
        """
        logger.info("Checking if manufacturer with code '%s' already exists", code)
        manufacturer = self._manufacturers_collection.find_one(
            {"code": code, "_id": {"$ne": manufacturer_id}}, session=session
        )
        return manufacturer is not None

    def _is_manufacturer_in_catalogue_item(self, manufacturer_id: str, session: ClientSession = None) -> bool:
        """
        Check if a manufacturer is part of a catalogue item based on its ID.

        :param manufacturer_id: The ID of the manufacturer to check.
        :param session: PyMongo ClientSession to use for database operations.
        :return: `True` if the manufacturer is part of a catalogue item, `False` otherwise.
        """
        manufacturer_id = CustomObjectId(manufacturer_id)
        return (
            self._catalogue_items_collection.find_one({"manufacturer_id": manufacturer_id}, session=session) is not None
        )
