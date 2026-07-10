from __future__ import annotations

from collections.abc import Mapping
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict

EXPECTED_NAMESPACE = "KaboKableMolefe"
EXPECTED_CONFIRMATION = "PUBLISH_EXACT_DATASET"
EXPECTED_GITHUB_REF = "refs/heads/main"


class StrictWorkflowGateModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class WorkflowPublicationGate(StrictWorkflowGateModel):
    namespace: Literal["KaboKableMolefe"]
    confirmation: Literal["PUBLISH_EXACT_DATASET"]
    git_ref: Literal["refs/heads/main"]
    credential_present: Literal[True]


class WorkflowPublicationGateErrorCode(StrEnum):
    NAMESPACE_MISMATCH = "hf_workflow_namespace_mismatch"
    CONFIRMATION_MISMATCH = "hf_workflow_confirmation_mismatch"
    REF_NOT_MAIN = "hf_workflow_ref_not_main"
    CREDENTIAL_MISSING = "hf_workflow_credential_missing"


class WorkflowPublicationGateError(RuntimeError):
    def __init__(
        self,
        code: WorkflowPublicationGateErrorCode,
        message: str,
    ) -> None:
        super().__init__(message)
        self.code = code


def validate_workflow_environment(
    environment: Mapping[str, str],
) -> WorkflowPublicationGate:
    namespace = environment.get("REQUESTED_NAMESPACE", "").strip()
    if namespace != EXPECTED_NAMESPACE:
        raise WorkflowPublicationGateError(
            WorkflowPublicationGateErrorCode.NAMESPACE_MISMATCH,
            f"requested namespace must be exactly {EXPECTED_NAMESPACE}",
        )

    confirmation = environment.get("PUBLICATION_CONFIRMATION", "").strip()
    if confirmation != EXPECTED_CONFIRMATION:
        raise WorkflowPublicationGateError(
            WorkflowPublicationGateErrorCode.CONFIRMATION_MISMATCH,
            f"publication confirmation must be exactly {EXPECTED_CONFIRMATION}",
        )

    git_ref = environment.get("GITHUB_REF", "").strip()
    if git_ref != EXPECTED_GITHUB_REF:
        raise WorkflowPublicationGateError(
            WorkflowPublicationGateErrorCode.REF_NOT_MAIN,
            "Hugging Face publication may run only from the main branch",
        )

    if not environment.get("HF_TOKEN", "").strip():
        raise WorkflowPublicationGateError(
            WorkflowPublicationGateErrorCode.CREDENTIAL_MISSING,
            "the protected HF_TOKEN environment secret is missing",
        )

    return WorkflowPublicationGate(
        namespace=EXPECTED_NAMESPACE,
        confirmation=EXPECTED_CONFIRMATION,
        git_ref=EXPECTED_GITHUB_REF,
        credential_present=True,
    )
