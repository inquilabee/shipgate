"""CLI option serialization."""

from shipgate.domain.catalog import CliOptionDefinition


class CliSerializer:
    """Serialize normalized option values into argv fragments."""

    def serialize(self, definition: CliOptionDefinition, value: object) -> list[str]:
        if value is None:
            return []
        style = definition.style
        return (
            self._serialize_boolean(definition, value)
            if style == "boolean"
            else (
                self._serialize_positional(value)
                if style == "positional"
                else (
                    (
                        self._serialize_scalar(definition, value)
                        if style == "scalar"
                        else (
                            self._serialize_repeated(definition, value)
                            if style == "repeated"
                            else (
                                self._serialize_joined(definition, value)
                                if style == "joined"
                                else []
                            )
                        )
                    )
                    if definition.flag
                    else []
                )
            )
        )

    @staticmethod
    def _serialize_boolean(definition: CliOptionDefinition, value: object) -> list[str]:
        return ([definition.flag] if definition.flag else []) if value else []

    @staticmethod
    def _serialize_positional(value: object) -> list[str]:
        return [str(v) for v in value] if isinstance(value, (list, tuple)) else [str(value)]

    @staticmethod
    def _serialize_scalar(definition: CliOptionDefinition, value: object) -> list[str]:
        if not definition.flag:
            return []
        flag = definition.flag
        if isinstance(value, (list, tuple)):
            if not value:
                return []
            # aggregate == "repeat" or bare multi-value: emit every entry.
            # aggregate == "root" is handled earlier by aggregate_value().
            if definition.aggregate in (None, "repeat"):
                result: list[str] = []
                for item in value:
                    result.extend([flag, str(item)])
                return result
            value = value[0]
        return [flag, str(value)]

    @staticmethod
    def _serialize_repeated(definition: CliOptionDefinition, value: object) -> list[str]:
        if not definition.flag:
            return []
        flag = definition.flag
        values = value if isinstance(value, (list, tuple)) else (value,)
        result: list[str] = []
        for item in values:
            result.extend([flag, str(item)])
        return result

    @staticmethod
    def _serialize_joined(definition: CliOptionDefinition, value: object) -> list[str]:
        if not definition.flag:
            return []
        flag = definition.flag
        values = value if isinstance(value, (list, tuple)) else (value,)
        joined = definition.separator.join(str(v) for v in values)
        return [flag, joined]


DEFAULT_SERIALIZER = CliSerializer()


def serialize_option(definition: CliOptionDefinition, value: object) -> list[str]:
    return DEFAULT_SERIALIZER.serialize(definition, value)
