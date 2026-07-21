"""CLI option serialization."""

from shipgate.domain.catalog import CliOptionDefinition


def serialize_option(
    definition: CliOptionDefinition,
    value: object,
) -> list[str]:
    style = definition.style
    if value is None:
        return []
    if style == "boolean":
        return _serialize_boolean(definition, value)
    if style == "positional":
        return _serialize_positional(value)
    if not definition.flag:
        return []
    if style == "scalar":
        return _serialize_scalar(definition, value)
    if style == "repeated":
        return _serialize_repeated(definition, value)
    if style == "joined":
        return _serialize_joined(definition, value)
    return []


def _serialize_boolean(definition: CliOptionDefinition, value: object) -> list[str]:
    if value:
        return [definition.flag] if definition.flag else []
    return []


def _serialize_positional(value: object) -> list[str]:
    if isinstance(value, (list, tuple)):
        return [str(v) for v in value]
    return [str(value)]


def _serialize_scalar(definition: CliOptionDefinition, value: object) -> list[str]:
    if not definition.flag:
        return []
    flag = definition.flag
    if isinstance(value, (list, tuple)):
        if not value:
            return []
        value = value[0]
    return [flag, str(value)]


def _serialize_repeated(definition: CliOptionDefinition, value: object) -> list[str]:
    if not definition.flag:
        return []
    flag = definition.flag
    values = value if isinstance(value, (list, tuple)) else (value,)
    result: list[str] = []
    for item in values:
        result.extend([flag, str(item)])
    return result


def _serialize_joined(definition: CliOptionDefinition, value: object) -> list[str]:
    if not definition.flag:
        return []
    flag = definition.flag
    values = value if isinstance(value, (list, tuple)) else (value,)
    joined = definition.separator.join(str(v) for v in values)
    return [flag, joined]
