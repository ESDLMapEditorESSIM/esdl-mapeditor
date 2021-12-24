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

from typing import List, Optional, Union
from uuid import uuid4

from esdlproject import BaseVariant, Variant


def get_parent_variant(variant: Variant) -> Union[BaseVariant, Variant]:
    """
    Return the parent variant or the base variant of this variant.
    """
    if variant.parentVariant is None and variant.baseVariant is not None:
        return variant.baseVariant
    else:
        return variant.parentVariant


def create_new_variant(parentVariant: Union[BaseVariant, Variant], variant_name: Optional[str] = None) -> Variant:
    """
    Create a new variant under a base variant or variant.
    """
    if variant_name is None:
        variant_name = f"Untitled variant {len(parentVariant.variant) + 1}"
    new_variant = Variant(name=variant_name, id=str(uuid4()))
    parentVariant.variant.append(new_variant)
    return new_variant


def get_variant_path_list(variant: Variant) -> List[Variant]:
    """
    Calculates the variants between this variant and its base variant and returns them as a list.
    """
    variant_list = [variant]
    current_variant = variant
    while current_variant.parentVariant:
        variant_list.append(current_variant.parentVariant)
        current_variant = current_variant.parentVariant
    return variant_list
