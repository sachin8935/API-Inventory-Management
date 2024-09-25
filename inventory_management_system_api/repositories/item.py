"""
Module for providing a repository for managing items in a MongoDB database.
"""

import logging
from datetime import datetime, timezone
from typing import List, Optional

from bson import ObjectId
from pymongo.client_session import ClientSession
from pymongo.collection import Collection

from inventory_management_system_api.core.custom_object_id import CustomObjectId
from inventory_management_system_api.core.database import DatabaseDep
from inventory_management_system_api.core.exceptions import MissingRecordError
from inventory_management_system_api.models.catalogue_item import PropertyIn
from inventory_management_system_api.models.item import ItemIn, ItemOut

logger = logging.getLogger()


class ItemRepo:
    """
    Repository for managing items in a MongoDB database.
    """

    def __init__(self, database: DatabaseDep) -> None:
        """
        Initialize the `ItemRepo` with a MongoDB database instance.

        :param database: The database to use.
        """
        self._database = database
        self._items_collection: Collection = self._database.items
        self._systems_collection: Collection = self._database.systems

    def create(self, item: ItemIn, session: ClientSession = None) -> ItemOut:
        """
        Create a new item in a MongoDB database.

        :param item: The item to be created.
        :param session: PyMongo ClientSession to use for database operations
        :return: The created item.
        """
        if item.system_id and not self._systems_collection.find_one({"_id": item.system_id}, session=session):
            raise MissingRecordError(f"No system found with ID: {item.system_id}")

        logger.info("Inserting the new item into the database")
        result = self._items_collection.insert_one(item.model_dump(by_alias=True), session=session)

        item = self.get(str(result.inserted_id), session=session)
        return item

    def get(self, item_id: str, session: ClientSession = None) -> Optional[ItemOut]:
        """
        Retrieve an item by its ID from a MongoDB database.

        :param item_id: The ID of the item to retrieve
        :param session: PyMongo ClientSession to use for database operations
        :return: The retrieved item, or `None` if not found.
        """
        item_id = CustomObjectId(item_id)
        logger.info("Retrieving item with ID %s from the database", item_id)
        item = self._items_collection.find_one({"_id": item_id}, session=session)
        if item:
            return ItemOut(**item)
        return None

    def list(
        self, system_id: Optional[str], catalogue_item_id: Optional[str], session: ClientSession = None
    ) -> List[ItemOut]:
        """
        Get all items from the MongoDB database

        :param system_id: The ID of the system to filter items by.
        :param catalogue_item_id: The ID of the catalogue item to filter by.
        :param session: PyMongo ClientSession to use for database operations
        :return List of items, or empty list if there are no items
        """
        query = {}
        if system_id:
            query["system_id"] = CustomObjectId(system_id)

        if catalogue_item_id:
            catalogue_item_id = CustomObjectId(catalogue_item_id)
            query["catalogue_item_id"] = catalogue_item_id

        message = "Retrieving all items from the database"
        if not query:
            logger.info(message)
        else:
            logger.info("%s matching the provided system ID and/or catalogue item ID filter", message)
            if system_id:
                logger.debug("Provided system ID filter: %s", system_id)
            if catalogue_item_id:
                logger.debug("Provided catalogue item ID filter: %s", catalogue_item_id)

        items = self._items_collection.find(query, session=session)
        return [ItemOut(**item) for item in items]

    def update(self, item_id: str, item: ItemIn, session: ClientSession = None) -> ItemOut:
        """
        Update an item by its ID in a MongoDB database.

        :param item_id: The ID of the item to update.
        :param item: The item containing the update data.
        :param session: PyMongo ClientSession to use for database operations
        :return: The updated item.
        """
        item_id = CustomObjectId(item_id)
        logger.info("Updating item with ID: %s in the database", item_id)
        self._items_collection.update_one({"_id": item_id}, {"$set": item.model_dump(by_alias=True)}, session=session)
        item = self.get(str(item_id), session=session)
        return item

    def delete(self, item_id: str, session: ClientSession = None) -> None:
        """
        Delete an item by its ID from a MongoDB database.

        :param item_id: The ID of the item to delete.
        :param session: PyMongo ClientSession to use for database operations
        :raises MissingRecordError: If the item doesn't exist
        """
        item_id = CustomObjectId(item_id)
        logger.info("Deleting item with ID: %s from the database", item_id)
        result = self._items_collection.delete_one({"_id": item_id}, session=session)
        if result.deleted_count == 0:
            raise MissingRecordError(f"No item found with ID: {str(item_id)}")

    def insert_property_to_all_in(
        self, catalogue_item_ids: List[ObjectId], property_in: PropertyIn, session: ClientSession = None
    ):
        """
        Inserts a property into every item with one of the given catalogue_item_id's using an update_many query

        :param catalogue_item_ids: List of catalogue_item_id's to look for in the items that the property should be
                                   added to
        :param property_in: The property to insert into the items' properties list
        :param session: PyMongo ClientSession to use for database operations
        """

        # This log should happen after the corresponding one finding the ids during a property addition, don't log
        # all the ids as there could be many
        logger.info(
            "Inserting property into corresponding items of the catalogue items",
        )
        self._items_collection.update_many(
            {"catalogue_item_id": {"$in": catalogue_item_ids}},
            {
                "$push": {"properties": property_in.model_dump(by_alias=True)},
                "$set": {"modified_time": datetime.now(timezone.utc)},
            },
            session=session,
        )

    # pylint:disable=duplicate-code
    def update_names_of_all_properties_with_id(
        self, property_id: str, new_property_name: str, session: ClientSession = None
    ) -> None:
        """
        Updates the name of a property in every item it is present in

        Also updates the modified_time to reflect the update

        :param property_id: The ID of the property to update
        :param new_property_name: The new property name
        :param session: PyMongo ClientSession to use for database operations
        """

        logger.info("Updating all properties with ID: %s inside items in the database", property_id)

        self._items_collection.update_many(
            {"properties._id": CustomObjectId(property_id)},
            {
                "$set": {
                    "properties.$[elem].name": new_property_name,
                    "modified_time": datetime.now(timezone.utc),
                }
            },
            array_filters=[{"elem._id": CustomObjectId(property_id)}],
            session=session,
        )

    # pylint:enable=duplicate-code
