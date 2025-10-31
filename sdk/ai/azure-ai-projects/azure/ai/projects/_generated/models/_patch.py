# ------------------------------------
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
# ------------------------------------
"""Customize generated code here.

Follow our quickstart for examples: https://aka.ms/azsdk/python/dpcodegen/python/customize
"""
from typing import List, Dict
from enum import Enum
from ._models import CustomCredential as CustomCredentialGenerated
from azure.core import CaseInsensitiveEnumMeta


# TODO: Are these needed?
class EvaluatorIds(str, Enum, metaclass=CaseInsensitiveEnumMeta):
    RELEVANCE = "azureai://built-in/evaluators/relevance"
    HATE_UNFAIRNESS = "azureai://built-in/evaluators/hate_unfairness"
    VIOLENCE = "azureai://built-in/evaluators/violence"
    GROUNDEDNESS = "azureai://built-in/evaluators/groundedness"
    GROUNDEDNESS_PRO = "azureai://built-in/evaluators/groundedness_pro"
    BLEU_SCORE = "azureai://built-in/evaluators/bleu_score"
    CODE_VULNERABILITY = "azureai://built-in/evaluators/code_vulnerability"
    COHERENCE = "azureai://built-in/evaluators/coherence"
    CONTENT_SAFETY = "azureai://built-in/evaluators/content_safety"
    F1_SCORE = "azureai://built-in/evaluators/f1_score"
    FLUENCY = "azureai://built-in/evaluators/fluency"
    GLEU_SCORE = "azureai://built-in/evaluators/gleu_score"
    INDIRECT_ATTACK = "azureai://built-in/evaluators/indirect_attack"
    INTENT_RESOLUTION = "azureai://built-in/evaluators/intent_resolution"
    METEOR_SCORE = "azureai://built-in/evaluators/meteor_score"
    PROTECTED_MATERIAL = "azureai://built-in/evaluators/protected_material"
    RETRIEVAL = "azureai://built-in/evaluators/retrieval"
    ROUGE_SCORE = "azureai://built-in/evaluators/rouge_score"
    SELF_HARM = "azureai://built-in/evaluators/self_harm"
    SEXUAL = "azureai://built-in/evaluators/sexual"
    SIMILARITY = "azureai://built-in/evaluators/similarity"
    QA = "azureai://built-in/evaluators/qa"
    DOCUMENT_RETRIEVAL = "azureai://built-in/evaluators/document_retrieval"
    TASK_ADHERENCE = "azureai://built-in/evaluators/task_adherence"
    TOOL_CALL_ACCURACY = "azureai://built-in/evaluators/tool_call_accuracy"
    UNGROUNDED_ATTRIBUTES = "azureai://built-in/evaluators/ungrounded_attributes"
    RESPONSE_COMPLETENESS = "azureai://built-in/evaluators/response_completeness"
    # AOAI Graders
    LABEL_GRADER = "azureai://built-in/evaluators/azure-openai/label_grader"
    STRING_CHECK_GRADER = "azureai://built-in/evaluators/azure-openai/string_check_grader"
    TEXT_SIMILARITY_GRADER = "azureai://built-in/evaluators/azure-openai/text_similarity_grader"
    GENERAL_GRADER = "azureai://built-in/evaluators/azure-openai/custom_grader"
    SCORE_MODEL_GRADER = "azureai://built-in/evaluators/azure-openai/score_model_grader"


class CustomCredential(CustomCredentialGenerated):
    """Custom credential definition.

    :ivar type: The credential type. Always equals CredentialType.CUSTOM. Required.
    :vartype type: str or ~azure.ai.projects.models.CredentialType
    :ivar credential_keys: The secret custom credential keys. Required.
    :vartype credential_keys: dict[str, str]
    """

    credential_keys: Dict[str, str] = {}
    """The secret custom credential keys. Required."""


__all__: List[str] = [
    "EvaluatorIds",
    "CustomCredential",
]  # Add all objects you want publicly available to users at this package level


def patch_sdk():
    """Do not remove from this file.

    `patch_sdk` is a last resort escape hatch that allows you to do customizations
    you can't accomplish using the techniques described in
    https://aka.ms/azsdk/python/dpcodegen/python/customize
    """
