import esdl

# Fields exposed per constraint type in the table editor
CONSTRAINT_FIELDS = {
    'RangedConstraint': ['name', 'attributeReference', 'range.minValue', 'range.maxValue', 'range.midValue'],
    'PipeDiameterConstraint': ['name', 'attributeReference', 'minimum', 'maximum'],
    'ProfileConstraint': ['name'],
}

READONLY_CONSTRAINT_TYPES = {'ProfileConstraint'}

PIPE_DIAMETER_OPTIONS = [{'label': lit.name, 'value': lit.name} for lit in esdl.PipeDiameterEnum.eLiterals]


def get_constraint_information(asset):
    """
    Extract constraint information from an asset for the Table Editor.

    :param asset: an ESDL asset object
    :return: list of dicts with type-specific constraint fields
    """
    if not hasattr(asset, 'constraint'):
        return []

    result = []
    for c in asset.constraint:
        entry = {
            'type': c.eClass.name,
            'name': c.name or '',
            'attributeReference': c.attributeReference or '',
        }
        if c.eClass.name == 'RangedConstraint':
            r = c.range
            entry['range.minValue'] = r.minValue if r else None
            entry['range.maxValue'] = r.maxValue if r else None
            entry['range.midValue'] = r.midValue if r else None
        elif c.eClass.name == 'PipeDiameterConstraint':
            entry['minimum'] = str(c.minimum) if c.minimum else ''
            entry['maximum'] = str(c.maximum) if c.maximum else ''
        elif c.eClass.name == 'ProfileConstraint':
            pass  # ProfileConstraint can be very hierarchical; so only expose the name and attributeReference for now
        result.append(entry)
    return result


def get_constraint_type_counts(asset_info_list):
    """
    Determine the max instance count per constraint type across all assets.

    :param asset_info_list: list of asset info dicts (with 'constraint_information' key)
    :return: dict mapping constraint type name to max instance count (insertion-ordered)
    """
    max_counts = {}
    for asset in asset_info_list:
        type_counts = {}
        for c in asset.get('constraint_information', []):
            ctype = c['type']
            type_counts[ctype] = type_counts.get(ctype, 0) + 1
        for ctype, count in type_counts.items():
            if count > max_counts.get(ctype, 0):
                max_counts[ctype] = count
    return max_counts


def get_constraint_column_info(asset_info_list):
    """
    Generate column definitions for constraints in the table editor.

    :param asset_info_list: list of asset info dicts
    :return: list of column dicts for the revogrid datagrid
    """
    columns = []
    constraint_meta = get_constraint_type_counts(asset_info_list)

    for ctype, max_count in constraint_meta.items():
        fields = CONSTRAINT_FIELDS.get(ctype, ['name'])
        readonly = ctype in READONLY_CONSTRAINT_TYPES
        for idx in range(max_count):
            for field in fields:
                column = {
                    'name': f"{ctype}[{idx}].{field}",
                    'prop': f"constraint.{ctype}.{idx}.{field}",
                    'readonly': readonly,
                }
                if field in ('name', 'attributeReference'):
                    column['autoSize'] = True
                if ctype == 'PipeDiameterConstraint' and field in ('minimum', 'maximum'):
                    column['options'] = PIPE_DIAMETER_OPTIONS
                columns.append(column)
    return columns


def get_constraint_row_data(asset_attr_info, constraint_meta):
    """
    Populate constraint cell values for a single asset row.

    :param asset_attr_info: single asset info dict (with 'constraint_information' key)
    :param constraint_meta: dict from get_constraint_type_counts
    :return: dict of prop->value pairs to merge into the row
    """
    row = {}
    constraint_by_type = {}
    for c in asset_attr_info.get('constraint_information', []):
        constraint_by_type.setdefault(c['type'], []).append(c)

    for ctype, max_count in constraint_meta.items():
        fields = CONSTRAINT_FIELDS.get(ctype, ['name'])
        instances = constraint_by_type.get(ctype, [])
        for idx in range(max_count):
            for field in fields:
                prop = f"constraint.{ctype}.{idx}.{field}"
                if idx < len(instances):
                    val = instances[idx].get(field, '')
                    row[prop] = val if val is not None else ''
                else:
                    row[prop] = ''
    return row
