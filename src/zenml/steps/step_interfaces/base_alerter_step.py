#  Copyright (c) ZenML GmbH 2021. All Rights Reserved.
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
"""Base alerter step."""

from abc import abstractmethod

from zenml.steps import BaseStep, BaseStepConfig, StepContext


class BaseAlerterStepConfig(BaseStepConfig):
    """Step config definition for all alerters."""


class BaseAlerterStep(BaseStep):
    """Send a message to the configured chat service."""

    @abstractmethod
    def entrypoint(  # type: ignore[override]
        self,
        message: str,
        config: BaseAlerterStepConfig,
        context: StepContext,
    ) -> bool:
        """Entrypoint for an Alerter step.

        Args:
            message: The message to send.
            config: The configuration for the step.
            context: The context for the step.

        Returns:
            True if the message was sent successfully.
        """
