from variation import Project, Variant


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
        children=[serialize_project_variant(variant) for variant in variant.variant]
    )
