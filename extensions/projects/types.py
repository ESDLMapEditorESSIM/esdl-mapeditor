from variation import Project, Variant, AbstractChange, HighLevelChange, DetailedChange


def serialize_project(project: Project) -> dict:
    """
    Serialize a project for usage in the frontend.
    """
    return dict(
        name=project.name,
        description=project.description,
        # TODO: We only support a single base variant. Should be reflected in Python model as well.
        base_variant=serialize_project_variant(project.variants[0]),
    )


def serialize_project_variant(variant: Variant) -> dict:
    """
    Serialize a project variant for usage in the frontend.
    """
    return dict(
        name=variant.name,
        description=variant.description,
        nr_of_changes=len(variant.changes),
        children=[serialize_project_variant(variant) for variant in variant.variant],
        changes=[serialize_abstract_change(change) for change in variant.changes],
    )


def serialize_abstract_change(change: AbstractChange) -> dict:
    """
    Serialize an abstract for usage in the frontend.
    """
    if isinstance(change, HighLevelChange):
        return serialize_high_level_change(change)
    else:
        return serialize_detailed_change(change)


def serialize_high_level_change(change: HighLevelChange) -> dict:
    """
    Serialize an abstract for usage in the frontend.
    """
    return dict(
        type="HighLevelChange",
        label=change.label,
        # changedAt=change.changedAt,
        changes=[serialize_abstract_change(change) for change in change.changes],
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
