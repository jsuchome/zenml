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
"""The base class for feature stores."""

from abc import ABC, abstractmethod
from typing import Any, ClassVar, Dict, List, Union

import pandas as pd

from zenml.enums import StackComponentType
from zenml.stack import StackComponent


class BaseFeatureStore(StackComponent, ABC):
    """Base class for all ZenML feature stores."""

    TYPE: ClassVar[StackComponentType] = StackComponentType.FEATURE_STORE
    FLAVOR: ClassVar[str]

    @abstractmethod
    def get_historical_features(
        self,
        entity_df: Union[pd.DataFrame, str],
        features: List[str],
        full_feature_names: bool = False,
    ) -> pd.DataFrame:
        """Returns the historical features for training or batch scoring.

        Args:
            entity_df: The entity DataFrame or entity name.
            features: The features to retrieve.
            full_feature_names: Whether to return the full feature names.

        Returns:
            The historical features as a Pandas DataFrame.
        """

    @abstractmethod
    def get_online_features(
        self,
        entity_rows: List[Dict[str, Any]],
        features: List[str],
        full_feature_names: bool = False,
    ) -> Dict[str, Any]:
        """Returns the latest online feature data.

        Args:
            entity_rows: The entity rows to retrieve.
            features: The features to retrieve.
            full_feature_names: Whether to return the full feature names.

        Returns:
            The latest online feature data as a dictionary.
        """
