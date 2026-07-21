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
        if value:
            return [definition.flag] if definition.flag else []
        return []
    if style == "positional":
        if isinstance(value, (list, tuple)):
            return [str(v) for v in value]
        return [str(value)]
    if not definition.flag:
        return []
    if style == "scalar":
        if isinstance(value, (list, tuple)):
            if not value:
                return []
            value = value[0]
        return [definition.flag, str(value)]
    if style == "repeated":
        values = value if isinstance(value, (list, tuple)) else (value,)
        result: list[str] = []
        for item in values:
            result.extend([definition.flag, str(item)])
        return result
    if style == "joined":
        values = value if isinstance(value, (list, tuple)) else (value,)
        joined = definition.separator.join(str(v) for v in values)
        return [definition.flag, joined]
    return []
