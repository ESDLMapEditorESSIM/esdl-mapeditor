#  This work is based on original code developed and copyrighted by TNO.
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

from __future__ import annotations

from enum import Enum
from uuid import uuid4

from pyecore.resources import ResourceSet

from esdl.processing.string_uri import StringURI
from extensions.prompt_manager import Prompt, PromptChoice, PromptType
from esdlproject.ProjectManager import ProjectManager


class DuplicateChoice(str, Enum):
    OVERWRITE = "overwrite"
    CANCEL = "cancel"
    RENAME = "rename"


def build_conflict_message(match_id: bool, match_name: bool, matched_es) -> str:
    """Build a human-readable conflict description."""
    if match_id and match_name:
        return (
            f"Conflict: ID and name match an existing energy system "
            f"('{matched_es.name}', ID {matched_es.id})."
        )
    if match_id:
        return (
            f"Conflict: ID matches existing energy system '{matched_es.name}' "
            f"(ID {matched_es.id})."
        )
    return f"Conflict: name matches existing energy system '{matched_es.name}'."


class DuplicatePrompt(Prompt):
    """Prompt shown when an imported ESDL conflicts with an existing one."""

    def __init__(
        self,
        user_email: str,
        continuation_id: str,
        match_id: bool,
        match_name: bool,
        matched_es,
        context: dict | None = None,
        details: str | None = None,
    ):
        super().__init__(
            prompt_type=PromptType.CHOICE,
            title="Duplicate ESDL Detected",
            message=build_conflict_message(match_id, match_name, matched_es),
            choices=[
                PromptChoice(DuplicateChoice.CANCEL, "Cancel import"),
                PromptChoice(DuplicateChoice.OVERWRITE, "Overwrite existing", "danger"),
                PromptChoice(DuplicateChoice.RENAME, "Add with new name/ID", "primary"),
            ],
            user_email=user_email,
            continuation_id=continuation_id,
            context=context or {},
            details=details,
        )


def find_duplicate_variant_collection(pm: ProjectManager, es_id: str, es_name: str):
    """Find a VariantCollection that conflicts on ES id or name."""
    for variant_collection in pm.project.variantCollection:
        base_es = variant_collection.energysystemRef
        if base_es is None:
            continue
        match_id = base_es.id == es_id
        match_name = base_es.name == es_name
        if match_id or match_name:
            return variant_collection, match_id, match_name, base_es
    return None, False, False, None


def next_available_name(pm: ProjectManager, base_name: str) -> str:
    """Return base_name (N) where N is the lowest unused counter."""
    existing_names: set[str] = set()
    for vc in pm.project.variantCollection:
        if vc.energysystemRef is not None:
            existing_names.add(vc.energysystemRef.name)

    # Strip any existing counter suffix like " (3)" to get the true base.
    stripped = base_name
    if base_name.endswith(")"):
        paren_start = base_name.rfind("(")
        if paren_start > 0 and base_name[paren_start + 1:-1].strip().isdigit():
            stripped = base_name[:paren_start].rstrip()

    counter = 1
    while True:
        candidate = f"{stripped} ({counter})"
        if candidate not in existing_names:
            return candidate
        counter += 1


def generate_renamed_esdl_string(esdl_string: str, filename: str, new_name: str | None = None) -> str:
    """Return an ESDL string with a new EnergySystem id and optional name."""
    if not filename.endswith(".esdl") and not filename.endswith(".json"):
        filename = filename + ".esdl"

    uri = StringURI(filename, esdl_string)
    rset = ResourceSet()
    resource = rset.create_resource(uri)
    resource.load()

    es = resource.contents[0]
    es.id = str(uuid4())
    if new_name is not None:
        es.name = new_name

    resource.save()
    return uri.getvalue()
