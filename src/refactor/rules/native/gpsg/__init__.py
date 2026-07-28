"""GPSG native rules (optional ``gpsg`` pack)."""

from __future__ import annotations

from refactor.rules.native.gpsg.annotations import (
    RequireParameterAnnotationRule,
    RequireReturnAnnotationRule,
)
from refactor.rules.native.gpsg.decorators_properties import (
    AvoidTrivialPropertiesRule,
    DoNotUseStaticmethodRule,
)
from refactor.rules.native.gpsg.docstrings import (
    DocstringsForClassesRule,
    DocstringsForFunctionsRule,
    DocstringsForModulesRule,
    DocstringsForPackagesRule,
)
from refactor.rules.native.gpsg.lambda_style import (
    FilterLambdaToGeneratorRule,
    LambdasShouldBeShortRule,
    NoComplexIfExpressionsRule,
)
from refactor.rules.native.gpsg.naming import (
    AvoidSingleCharacterNamesFunctionsRule,
    AvoidSingleCharacterNamesVariablesRule,
    NameTypeSuffixRule,
    SnakeCaseArgumentsRule,
    SnakeCaseFunctionsRule,
    SnakeCaseVariableDeclarationsRule,
    UpperCamelCaseClassesRule,
)

RULES = (
    LambdasShouldBeShortRule(),
    FilterLambdaToGeneratorRule(),
    NoComplexIfExpressionsRule(),
    DoNotUseStaticmethodRule(),
    RequireParameterAnnotationRule(),
    RequireReturnAnnotationRule(),
    DocstringsForClassesRule(),
    DocstringsForFunctionsRule(),
    DocstringsForPackagesRule(),
    DocstringsForModulesRule(),
    AvoidTrivialPropertiesRule(),
    AvoidSingleCharacterNamesVariablesRule(),
    AvoidSingleCharacterNamesFunctionsRule(),
    NameTypeSuffixRule(),
    SnakeCaseVariableDeclarationsRule(),
    SnakeCaseArgumentsRule(),
    SnakeCaseFunctionsRule(),
    UpperCamelCaseClassesRule(),
)

__all__ = ["RULES"]
