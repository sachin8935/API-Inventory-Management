"""
Module for defining the API schema models for representing items.
"""

from typing import Optional, List

from pydantic import BaseModel, Field, AwareDatetime

from inventory_management_system_api.schemas.catalogue_item import PropertyPostSchema, PropertySchema
from inventory_management_system_api.schemas.mixins import CreatedModifiedSchemaMixin


class ItemPostSchema(BaseModel):
    """
    Schema model for an item creation request.
    """

    catalogue_item_id: str = Field(description="The ID of the corresponding catalogue item for this item")
    system_id: str = Field(description="The ID of the system that the item belongs to")
    purchase_order_number: Optional[str] = Field(default=None, description="The purchase order number of the item")
    is_defective: bool = Field(description="Whether the item is defective or not")
    usage_status_id: str = Field(description="The ID of the usage status of the item")
    warranty_end_date: Optional[AwareDatetime] = Field(default=None, description="The warranty end date of the item")
    asset_number: Optional[str] = Field(default=None, description="The asset number of the item")
    serial_number: Optional[str] = Field(default=None, description="The serial number of the item")
    delivered_date: Optional[AwareDatetime] = Field(default=None, description="The date the item was delivered")
    notes: Optional[str] = Field(default=None, description="Any notes about the item")
    properties: Optional[List[PropertyPostSchema]] = Field(
        default=None,
        description="The properties specific to this item as defined in the corresponding catalogue category. All "
        "properties found in the catalogue item will be inherited if not explicitly provided.",
    )


class ItemPatchSchema(ItemPostSchema):
    """
    Schema model for an item update request.
    """

    catalogue_item_id: Optional[str] = Field(
        default=None, description="The ID of the corresponding catalogue item for this item"
    )
    system_id: Optional[str] = Field(default=None, description="The ID of the system that the item belongs to")
    is_defective: Optional[bool] = Field(default=None, description="Whether the item is defective or not")
    usage_status_id: Optional[str] = Field(
        default=None,
        description="The ID of the usage status of the item.",
    )
    properties: Optional[List[PropertyPostSchema]] = Field(
        default=None,
        description="The properties specific to this item. Any properties not declared will be overwritten by "
        "the inherited properties from the catalogue item.",
    )


class ItemSchema(CreatedModifiedSchemaMixin, ItemPostSchema):
    """
    Schema model for an item response.
    """

    id: str = Field(description="The ID of the item")
    properties: List[PropertySchema] = Field(
        description="The properties specific to this item as defined in the corresponding catalogue category.",
    )
    usage_status: str
