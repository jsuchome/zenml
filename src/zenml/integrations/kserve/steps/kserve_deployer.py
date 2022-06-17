#  Copyright (c) ZenML GmbH 2022. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at:
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
#  or implied. See the License for the specific language governing
#  permissions and limitations under the License.
"""Implementation of the KServe Deployer step."""


import os
from typing import cast

from zenml.artifacts.model_artifact import ModelArtifact
from zenml.environment import Environment
from zenml.integrations.kserve.model_deployers.kserve_model_deployer import (
    DEFAULT_KSERVE_DEPLOYMENT_START_STOP_TIMEOUT,
    KServeModelDeployer,
)
from zenml.integrations.kserve.services.kserve_deployment import (
    KServeDeploymentConfig,
    KServeDeploymentService,
)
from zenml.io import fileio
from zenml.logger import get_logger
from zenml.steps import (
    STEP_ENVIRONMENT_NAME,
    BaseStepConfig,
    StepEnvironment,
    step,
)
from zenml.steps.step_context import StepContext
from zenml.utils import io_utils

logger = get_logger(__name__)


class KServeDeployerStepConfig(BaseStepConfig):
    """KServe model deployer step configuration.

    Attributes:
        service_config: KServe deployment service configuration.
        secrets: a list of ZenML secrets containing additional configuration
            parameters for the KServe deployment (e.g. credentials to
            access the Artifact Store where the models are stored). If supplied,
            the information fetched from these secrets is passed to the KServe
            deployment server as a list of environment variables.
    """

    service_config: KServeDeploymentConfig
    timeout: int = DEFAULT_KSERVE_DEPLOYMENT_START_STOP_TIMEOUT


@step(enable_cache=False)
def kserve_model_deployer_step(
    deploy_decision: bool,
    config: KServeDeployerStepConfig,
    context: StepContext,
    model: ModelArtifact,
) -> KServeDeploymentService:
    """KServe model deployer pipeline step.

    This step can be used in a pipeline to implement continuous
    deployment for a ML model with KServe.

    Args:
        deploy_decision: whether to deploy the model or not
        config: configuration for the deployer step
        model: the model artifact to deploy
        context: the step context

    Returns:
        KServe deployment service
    """
    model_deployer = KServeModelDeployer.get_active_model_deployer()

    # get pipeline name, step name and run id
    step_env = cast(StepEnvironment, Environment()[STEP_ENVIRONMENT_NAME])
    pipeline_name = step_env.pipeline_name
    pipeline_run_id = step_env.pipeline_run_id
    step_name = step_env.step_name

    # update the step configuration with the real pipeline runtime information
    config.service_config.pipeline_name = pipeline_name
    config.service_config.pipeline_run_id = pipeline_run_id
    config.service_config.pipeline_step_name = step_name

    def prepare_service_config(model_uri: str) -> KServeDeploymentConfig:
        """Prepare the model files for model serving.

        This function ensures that the model files are in the correct format
        and file structure required by the KServe server implementation
        used for model serving.

        Args:
            model_uri: the URI of the model artifact being served

        Returns:
            The URL to the model ready for serving.

        Raises:
            RuntimeError: if the model files cannot be prepared.
        """
        served_model_uri = os.path.join(
            context.get_output_artifact_uri(), "kserve"
        )
        fileio.makedirs(served_model_uri)

        # TODO [ENG-773]: determine how to formalize how models are organized into
        #   folders and sub-folders depending on the model type/format and the
        #   KServe protocol used to serve the model.

        # TODO [ENG-791]: auto-detect built-in KServe server implementation
        #   from the model artifact type

        # TODO [ENG-792]: validate the model artifact type against the
        #   supported built-in KServe server implementations
        if config.service_config.predictor == "tensorflow":
            # the TensorFlow server expects model artifacts to be
            # stored in numbered subdirectories, each representing a model
            # version
            io_utils.copy_dir(model_uri, os.path.join(served_model_uri, "1"))
        elif config.service_config.predictor == "sklearn":
            # the sklearn server expects model artifacts to be
            # stored in a file called model.joblib
            model_uri = os.path.join(model.uri, "model")
            if not fileio.exists(model.uri):
                raise RuntimeError(
                    f"Expected sklearn model artifact was not found at "
                    f"{model_uri}"
                )
            fileio.copy(
                model_uri, os.path.join(served_model_uri, "model.joblib")
            )
        else:
            # default treatment for all other server implementations is to
            # simply reuse the model from the artifact store path where it
            # is originally stored
            served_model_uri = model_uri

        service_config = config.service_config.copy()
        service_config.model_uri = served_model_uri
        return service_config

    # fetch existing services with same pipeline name, step name and
    # model name
    existing_services = model_deployer.find_model_server(
        pipeline_name=pipeline_name,
        pipeline_step_name=step_name,
        model_name=config.service_config.model_name,
    )

    # even when the deploy decision is negative, if an existing model server
    # is not running for this pipeline/step, we still have to serve the
    # current model, to ensure that a model server is available at all times
    if not deploy_decision and existing_services:
        logger.info(
            f"Skipping model deployment because the model quality does not "
            f"meet the criteria. Reusing last model server deployed by step "
            f"'{step_name}' and pipeline '{pipeline_name}' for model "
            f"'{config.service_config.model_name}'..."
        )
        service = cast(KServeDeploymentService, existing_services[0])
        # even when the deploy decision is negative, we still need to start
        # the previous model server if it is no longer running, to ensure that
        # a model server is available at all times
        if not service.is_running:
            service.start(timeout=config.timeout)
        return service

    # invoke the KServe model deployer to create a new service
    # or update an existing one that was previously deployed for the same
    # model
    service_config = prepare_service_config(model.uri)
    service = cast(
        KServeDeploymentService,
        model_deployer.deploy_model(
            service_config, replace=True, timeout=config.timeout
        ),
    )

    logger.info(
        f"KServe deployment service started and reachable at:\n"
        f"    {service.prediction_url}\n"
    )

    return service