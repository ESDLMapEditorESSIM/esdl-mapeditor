from esdlproject import ESDLProject, AbstractChange, HighLevelChange, DetailedChange, VariantCollection
from esdlproject.ProjectManager import ProjectManager


def serialize_esdl_project(pm: ProjectManager, project: ESDLProject) -> dict:
    """
    Serialize a project for usage in the frontend.
    """
    return dict(
        name=project.name,
        description=project.description,
        variants=[serialize_variant(pm, collection.variant) for collection in project.variantCollection],
        active_variant_id=pm.active_variant.id,
    )


# def serialize_variant_collection(pm: ProjectManager, collection: VariantCollection) -> dict:
#     """
#     Serialize a project variant for usage in the frontend.
#     """
#     return dict(
#         id=collection.id,
#         name=collection.name,
#         description=collection.description,
#         variants=[serialize_variant(pm, variant) for variant in collection.variant.variant],
#     )


def serialize_variant(pm: ProjectManager, variant: VariantCollection) -> dict:
    """
    Serialize a project variant for usage in the frontend.
    """
    active_variant = pm.active_variant
    return dict(
        id=variant.id,
        name=variant.name,
        description=variant.description,
        nr_of_changes=len(variant.change),
        es_id=variant.snapshotRef.id if variant.snapshotRef else None,
        active=active_variant.id == variant.id,
        children=[serialize_variant(pm, variant) for variant in variant.variant],
        changes=[],  # don't show changes anymore, TODO: update frontend code to remove this attribute
    )


def serialize_abstract_change(change: AbstractChange) -> dict:
    """
    Serialize an abstract for usage in the frontend.
    """
    if isinstance(change, HighLevelChange):
        return serialize_high_level_change(change)
    else:
        change: DetailedChange
        return serialize_detailed_change(change)


def serialize_high_level_change(change: HighLevelChange) -> dict:
    """
    Serialize an abstract for usage in the frontend.
    """
    return dict(
        type="HighLevelChange",
        label=change.label,
        # changedAt=change.changedAt,
        changes=[serialize_abstract_change(change) for change in change.change],
    )


def serialize_detailed_change(change: DetailedChange) -> dict:
    """
    Serialize an abstract for usage in the frontend.
    """
    return dict(
        type=change.__class__.__name__,
        feature=change.feature,
        object_value_type=change.objectValue.__class__.__name__ if change.objectValue else None,
    )
