import re


def get_nested_dict_value(dictionary: dict, nested_key: str) -> any:
    """
    Get dictionary value from a nested key, which consists of subsequent keys separated by a dot.

    :param dictionary: dictionary to get value from.
    :param nested_key: nested key which consists of subsequent keys separated by a dot.
    :return: dictionary value of the nested key.
    """
    if "." not in nested_key:
        if nested_key in dictionary:
            return dictionary[nested_key]
        else:
            return None
    else:
        top_key = nested_key.split(".", 1)[0]
        new_key = nested_key.split(".", 1)[1]
        if top_key in dictionary:
            return get_nested_dict_value(dictionary[top_key], new_key)
        else:
            return None


def parse_string_with_parameters(string: str, params_dict: dict) -> str:
    """
    Parse parameters, surrounded by `<>`, present in string.

    :param string: string to be parsed.
    :param params_dict: Key-values used for the parsing.
    :return: Parsed string.
    """
    replace_args = re.findall(r"<.*?>", string)
    for replace_arg in replace_args:
        string = string.replace(replace_arg, params_dict[replace_arg[1:-1].lower()])
    return string


def pretty_print_html(item_to_print: object, indent: str = "") -> str:
    """
    Pretty print dict, list or string, for display in html.

    :param item_to_print: Item to be printed, can be dict, list or string.
    :param indent: Indent before each line.
    :return: Pretty printed text
    """
    if not item_to_print:
        return "none"
    elif isinstance(item_to_print, dict):
        pretty = ""
        for k, v in item_to_print.items():
            pretty += f"<br>{indent}{k}: "
            if isinstance(v, dict) or isinstance(v, list):
                pretty += pretty_print_html(v, f"{indent}&emsp;")
            else:
                pretty += str(v)
        return pretty
    elif isinstance(item_to_print, list):
        v = [pretty_print_html(item) for item in item_to_print]
        return ", ".join(v)
    else:
        return str(item_to_print)
