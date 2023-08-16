from esdlproject import ESDLProject, Variant, ProjectEnergySystem, AbstractChange, HighLevelChange, DetailedChange
from esdlproject.ProjectManager import ProjectManager


def serialize_esdl_project(pm: ProjectManager, project: ESDLProject) -> dict:
    """
    Serialize a project for usage in the frontend.
    """
    return dict(
        name=project.name,
        description=project.description,
        base_variants=[serialize_base_variant(pm, base_variant) for base_variant in project.energySystem],
        active_variant_id=pm.active_variant.id,
    )


def serialize_base_variant(pm: ProjectManager, base_variant: ProjectEnergySystem) -> dict:
    """
    Serialize a project variant for usage in the frontend.
    """
    return dict(
        id=base_variant.id,
        name=base_variant.name,
        description=base_variant.description,
        variants=[serialize_variant(pm, variant) for variant in base_variant.variant],
    )


def serialize_variant(pm: ProjectManager, variant: Variant) -> dict:
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
        changes=[serialize_abstract_change(change) for change in variant.change],
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
