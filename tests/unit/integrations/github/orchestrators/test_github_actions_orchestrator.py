#  Copyright (c) ZenML GmbH 2022. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at:
#
#       https://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
#  or implied. See the License for the specific language governing
#  permissions and limitations under the License.

from contextlib import ExitStack as does_not_raise

import pytest

from zenml.container_registries import DefaultContainerRegistry
from zenml.enums import StackComponentType
from zenml.exceptions import StackValidationError
from zenml.integrations.gcp.artifact_stores import GCPArtifactStore
from zenml.integrations.github.orchestrators import GitHubActionsOrchestrator
from zenml.metadata_stores import MySQLMetadataStore, SQLiteMetadataStore
from zenml.stack import Stack


def test_github_actions_orchestrator_attributes() -> None:
    """Tests that the basic attributes of the GitHub actions orchestrator are
    set correctly."""
    orchestrator = GitHubActionsOrchestrator(name="")
    assert orchestrator.TYPE == StackComponentType.ORCHESTRATOR
    assert orchestrator.FLAVOR == "github"


def test_github_actions_orchestrator_stack_validation() -> None:
    """Tests the GitHub actions orchestrator stack validation."""
    orchestrator = GitHubActionsOrchestrator(name="")

    local_metadata_store = SQLiteMetadataStore(name="", uri="metadata.db")
    remote_metadata_store = MySQLMetadataStore(
        name="",
        username="",
        password="",
        host="",
        port=0,
        database="",
    )

    local_container_registry = DefaultContainerRegistry(
        name="", uri="localhost:5000"
    )
    container_registry_that_requires_authentication = DefaultContainerRegistry(
        name="", uri="localhost:5000", authentication_secret="some_secret"
    )
    remote_container_registry = DefaultContainerRegistry(
        name="", uri="gcr.io/my-project"
    )

    remote_artifact_store = GCPArtifactStore(name="", path="gs://bucket")

    with does_not_raise():
        # Stack with container registry and only remote components
        Stack(
            name="",
            orchestrator=orchestrator,
            metadata_store=remote_metadata_store,
            artifact_store=remote_artifact_store,
            container_registry=remote_container_registry,
        ).validate()

    with pytest.raises(StackValidationError):
        # Stack without container registry
        Stack(
            name="",
            orchestrator=orchestrator,
            metadata_store=remote_metadata_store,
            artifact_store=remote_artifact_store,
        ).validate()

    with pytest.raises(StackValidationError):
        # Stack with local container registry
        Stack(
            name="",
            orchestrator=orchestrator,
            metadata_store=remote_metadata_store,
            artifact_store=remote_artifact_store,
            container_registry=local_container_registry,
        ).validate()

    with pytest.raises(StackValidationError):
        # Stack with container registry that requires authentication
        Stack(
            name="",
            orchestrator=orchestrator,
            metadata_store=remote_metadata_store,
            artifact_store=remote_artifact_store,
            container_registry=container_registry_that_requires_authentication,
        ).validate()

    with pytest.raises(StackValidationError):
        # Stack with local components
        Stack(
            name="",
            orchestrator=orchestrator,
            metadata_store=local_metadata_store,
            artifact_store=remote_artifact_store,
            container_registry=remote_container_registry,
        ).validate()
