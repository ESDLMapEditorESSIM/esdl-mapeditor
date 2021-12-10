from esdlproject import ESDLProject, Variant, BaseVariant, AbstractChange, HighLevelChange, DetailedChange
from esdlproject.ProjectManager import ProjectManager


def serialize_esdl_project(pm: ProjectManager, project: ESDLProject) -> dict:
    """
    Serialize a project for usage in the frontend.
    """
    return dict(
        name=project.name,
        description=project.description,
        base_variants=[serialize_base_variant(pm, base_variant) for base_variant in project.baseVariant],
    )


def serialize_base_variant(pm: ProjectManager, base_variant: BaseVariant) -> dict:
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
    resource = pm.get_base_variant_resource(variant)
    es = resource.contents[0]
    active_es = pm.get_active_energy_system()
    return dict(
        base_variant_id=variant.baseVariant.id,
        name=variant.name,
        description=variant.description,
        nr_of_changes=len(variant.change),
        es_id=es.id,
        active=active_es.id == es.id,
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
        value=change.stringValue,
        # changedAt=change.changedAt,
    )
