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
"""Initialization for Feast integration.

The Feast integration offers a way to connect to a Feast Feature Store. ZenML
implements a dedicated stack component that you can access as part of your ZenML
steps in the usual ways.
"""
from typing import List

from zenml.enums import StackComponentType
from zenml.integrations.constants import FEAST
from zenml.integrations.integration import Integration
from zenml.zen_stores.models import FlavorWrapper

FEAST_FEATURE_STORE_FLAVOR = "feast"


class FeastIntegration(Integration):
    """Definition of Feast integration for ZenML."""

    NAME = FEAST
    REQUIREMENTS = ["feast[redis]>=0.19.4", "redis-server"]

    @classmethod
    def flavors(cls) -> List[FlavorWrapper]:
        """Declare the stack component flavors for the Feast integration.

        Returns:
            List of stack component flavors for this integration.
        """
        return [
            FlavorWrapper(
                name=FEAST_FEATURE_STORE_FLAVOR,
                source="zenml.integrations.feast.feature_store.FeastFeatureStore",
                type=StackComponentType.FEATURE_STORE,
                integration=cls.NAME,
            )
        ]


FeastIntegration.check_installation()
