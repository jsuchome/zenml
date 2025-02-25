# Copyright 2020 Google LLC. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
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
"""The `BaseArtifactStore` offers an interface for extending the ZenML artifact store."""
import textwrap
from abc import abstractmethod
from typing import (
    Any,
    Callable,
    ClassVar,
    Dict,
    Iterable,
    List,
    Optional,
    Set,
    Tuple,
    Union,
)

from pydantic import root_validator
from tfx.dsl.io.fileio import NotFoundError

from zenml.enums import StackComponentType
from zenml.exceptions import ArtifactStoreInterfaceError
from zenml.stack import StackComponent

PathType = Union[bytes, str]


def _catch_not_found_error(_func: Callable[..., Any]) -> Callable[..., Any]:
    """Utility decorator used for catching a `FileNotFoundError`.

    Error is converted to a `NotFoundError` in order to deal with the TFX
    exception handling.

    Args:
        _func: The function to decorate.

    Returns:
        The decorated function.
    """

    def inner_function(*args: Any, **kwargs: Any) -> Any:
        """Inner function for the decorator.

        It attempts to run the function
        wrapped by the decorator and catches the FileNotFoundError if it is
        thrown. In that case, the tfx.NotFoundError is raised instead.

        Args:
            *args: The positional arguments to pass to the function.
            **kwargs: The keyword arguments to pass to the function.

        Returns:
            The inner function.

        Raises:
            NotFoundError: If the function throws a FileNotFoundError.
        """
        try:
            return _func(*args, **kwargs)
        except FileNotFoundError as e:
            raise NotFoundError() from e

    return inner_function


class BaseArtifactStore(StackComponent):
    """Base class for all ZenML artifact stores.

    Attributes:
        path: The root path of the artifact store.
    """

    path: str

    # Class Configuration
    TYPE: ClassVar[StackComponentType] = StackComponentType.ARTIFACT_STORE
    SUPPORTED_SCHEMES: ClassVar[Set[str]]

    # --- User interface ---
    @abstractmethod
    def open(self, name: PathType, mode: str = "r") -> Any:
        """Open a file at the given path.

        Args:
            name: The path of the file to open.
            mode: The mode to open the file.

        Returns:
            The file object.
        """

    @abstractmethod
    def copyfile(
        self, src: PathType, dst: PathType, overwrite: bool = False
    ) -> None:
        """Copy a file from the source to the destination.

        Args:
            src: The source path.
            dst: The destination path.
            overwrite: Whether to overwrite the destination file if it exists.
        """

    @abstractmethod
    def exists(self, path: PathType) -> bool:
        """Checks if a path exists.

        Args:
            path: The path to check.

        Returns:
            `True` if the path exists.
        """

    @abstractmethod
    def glob(self, pattern: PathType) -> List[PathType]:
        """Gets the paths that match a glob pattern.

        Args:
            pattern: The glob pattern.

        Returns:
            The list of paths that match the pattern.
        """

    @abstractmethod
    def isdir(self, path: PathType) -> bool:
        """Returns whether the given path points to a directory.

        Args:
            path: The path to check.

        Returns:
            `True` if the path points to a directory.
        """

    @abstractmethod
    def listdir(self, path: PathType) -> List[PathType]:
        """Returns a list of files under a given directory in the filesystem.

        Args:
            path: The path to list.

        Returns:
            The list of files under the given path.
        """

    @abstractmethod
    def makedirs(self, path: PathType) -> None:
        """Make a directory at the given path, recursively creating parents.

        Args:
            path: The path to create.
        """

    @abstractmethod
    def mkdir(self, path: PathType) -> None:
        """Make a directory at the given path; parent directory must exist.

        Args:
            path: The path to create.
        """

    @abstractmethod
    def remove(self, path: PathType) -> None:
        """Remove the file at the given path. Dangerous operation.

        Args:
            path: The path to remove.
        """

    @abstractmethod
    def rename(
        self, src: PathType, dst: PathType, overwrite: bool = False
    ) -> None:
        """Rename source file to destination file.

        Args:
            src: The source path.
            dst: The destination path.
            overwrite: Whether to overwrite the destination file if it exists.
        """

    @abstractmethod
    def rmtree(self, path: PathType) -> None:
        """Deletes dir recursively. Dangerous operation.

        Args:
            path: The path to delete.
        """

    @abstractmethod
    def stat(self, path: PathType) -> Any:
        """Return the stat descriptor for a given file path.

        Args:
            path: The path to check.

        Returns:
            The stat descriptor.
        """

    @abstractmethod
    def walk(
        self,
        top: PathType,
        topdown: bool = True,
        onerror: Optional[Callable[..., None]] = None,
    ) -> Iterable[Tuple[PathType, List[PathType], List[PathType]]]:
        """Return an iterator that walks the contents of the given directory.

        Args:
            top: The path to walk.
            topdown: Whether to walk the top-down or bottom-up.
            onerror: The error handler.

        Returns:
            The iterator that walks the contents of the given directory.
        """

    # --- Internal interface ---
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initiate the Pydantic object and register the corresponding filesystem.

        Args:
            *args: The positional arguments to pass to the Pydantic object.
            **kwargs: The keyword arguments to pass to the Pydantic object.
        """
        super(BaseArtifactStore, self).__init__(*args, **kwargs)
        self._register()

    @root_validator(skip_on_failure=True)
    def _ensure_artifact_store(cls, values: Dict[str, Any]) -> Any:
        """Validator function for the Artifact Stores.

        Checks whether supported schemes are defined and the given path is
        supported.

        Args:
            values: The values to validate.

        Returns:
            The validated values.

        Raises:
            ArtifactStoreInterfaceError: If the scheme is not supported.
        """
        try:
            getattr(cls, "SUPPORTED_SCHEMES")
        except AttributeError:
            raise ArtifactStoreInterfaceError(
                "When you are working with any classes which subclass from "
                "'zenml.artifact_store.BaseArtifactStore' please make sure "
                "that your class has a ClassVar named `SUPPORTED_SCHEMES` "
                "which should hold a set of supported file schemes such "
                "as {'s3://'} or {'gcs://'}. \n"
                + textwrap.dedent(
                    """
                    When you are working with any classes which subclass from
                    zenml.artifact_store.BaseArtifactStore please make sure
                    that your class has a ClassVar named `SUPPORTED_SCHEMES`
                    which should hold a set of supported file schemes such
                    as {"s3://"} or {"gcs://"}.

                    Example:

                    class S3ArtifactStore(StackComponent):
                        ...
                        # Class Variables
                        SUPPORTED_SCHEMES: ClassVar[Set[str]] = {"s3://"}
                        ...
                    """
                )
            )
        if not any(values["path"].startswith(i) for i in cls.SUPPORTED_SCHEMES):
            raise ArtifactStoreInterfaceError(
                f"The path: '{values['path']}' you defined for your "
                f"artifact store is not supported by the implementation of "
                f"{cls.schema()['title']}, because it does not start with "
                f"one of its supported schemes: {cls.SUPPORTED_SCHEMES}."
            )

        return values

    def _register(self, priority: int = 5) -> None:
        """Create and register a filesystem within the TFX registry.

        Args:
            priority: The priority of the filesystem.
        """
        from tfx.dsl.io.filesystem import Filesystem
        from tfx.dsl.io.filesystem_registry import DEFAULT_FILESYSTEM_REGISTRY

        filesystem_class = type(
            self.__class__.__name__,
            (Filesystem,),
            {
                "SUPPORTED_SCHEMES": self.SUPPORTED_SCHEMES,
                "open": staticmethod(_catch_not_found_error(self.open)),
                "copy": staticmethod(_catch_not_found_error(self.copyfile)),
                "exists": staticmethod(self.exists),
                "glob": staticmethod(self.glob),
                "isdir": staticmethod(self.isdir),
                "listdir": staticmethod(_catch_not_found_error(self.listdir)),
                "makedirs": staticmethod(self.makedirs),
                "mkdir": staticmethod(_catch_not_found_error(self.mkdir)),
                "remove": staticmethod(_catch_not_found_error(self.remove)),
                "rename": staticmethod(_catch_not_found_error(self.rename)),
                "rmtree": staticmethod(_catch_not_found_error(self.rmtree)),
                "stat": staticmethod(_catch_not_found_error(self.stat)),
                "walk": staticmethod(_catch_not_found_error(self.walk)),
            },
        )

        DEFAULT_FILESYSTEM_REGISTRY.register(
            filesystem_class, priority=priority
        )
