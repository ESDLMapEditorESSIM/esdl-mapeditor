#  This work is based on original code developed and copyrighted by TNO 2020.
#  Subsequent contributions are licensed to you by the developers of such code and are
#  made available to the Project under one or several contributor license agreements.
#
#  This work is licensed to you under the Apache License, Version 2.0.
#  You may obtain a copy of the license at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Contributors:
#      TNO         - Initial implementation
#  Manager:
#      TNO
import logging
from datetime import datetime, timezone
from typing import List, Optional, Union
from uuid import uuid4

from esdlproject import VariantCollection, Variant

logger = logging.getLogger(__name__)


def get_parent_variant(variant: Variant) -> Union[VariantCollection, Variant]:
    """
    Return the parent variant or the base variant of this variant.

    :param variant: Variant to get the parent variant of.
    :return: Parent variant or energy system proxy.
    """
    if variant.parentVariant is None and variant.variantCollection is not None:
        return variant.variantCollection
    else:
        return variant.parentVariant


def create_new_variant(parent_variant: Union[VariantCollection, Variant], variant_name: Optional[str] = None, variant_id: str | None = None) -> Variant:
    """
    Create a new variant under an VariantCollection or Variant.

    :param parent_variant: VariantCollection or variant to create the new variant under.
    :param variant_name: Name of the new variant.
    :param variant_id: Optionally the ID of the new variant.
    :return: The new variant.
    """
    logger.info("Create new variant: parent=%s, name=%s, id=%s", parent_variant, variant_name, variant_id)
    if isinstance(parent_variant, VariantCollection):
        parent_variant = parent_variant.variant  #
    if variant_name is None:
        variant_name = f"{parent_variant.name} ({len(parent_variant.variant) + 1})"
    new_variant = Variant(name=variant_name, id=variant_id or str(uuid4()), lastChanged=datetime.now(timezone.utc))
    parent_variant.variant.append(new_variant)
    return new_variant


def get_variant_path_list(variant: Variant) -> List[Variant]:
    """
    Calculates the variants between this variant and its base variant and returns them as a list.

    :param variant: Variant to get the path of.
    :return: List of variants between this variant and its base variant.
    """
    if variant is None:
        return []

    variant_list = [variant]
    current_variant = variant
    while current_variant.parentVariant:
        variant_list.append(current_variant.parentVariant)
        current_variant = current_variant.parentVariant
    return variant_list
