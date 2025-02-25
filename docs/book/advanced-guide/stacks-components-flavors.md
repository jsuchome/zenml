---
description: Setting up your MLOps infrastructure
---

# Stacks, Components, Flavors

Machine learning in production is not just about designing and training models. It is a fractured space consisting of a wide variety of tasks ranging from experiment tracking to orchestration, from model deployment to monitoring, from drift detection to feature stores and much, much more than that. Even though there are already some seemingly well-established solutions for these tasks, it can become increasingly difficult to establish a running production system in a reliable and modular manner once all these solutions are brought together.

This is a problem which is especially critical when switching from a research setting to a production setting. For instance, due to a lack of standards, the time and resources invested in a small PoC-like project can completely to waste, if the initial system can not be transferred to a production-grade setting.

At **ZenML**, we believe that this is one of the most important and challenging problems in the field of MLOps, and it can be solved with a set of standards and well-structured abstractions. Owing to the nature of MLOps, it is essential that these abstractions not only cover concepts such as pipelines, steps and materializers which we covered in the previous guides but also the infrastructure elements that on which the pipelines run.

Taking this into consideration, we will introduce three major concepts that ZenML is based on: **Stacks**, **Stack Components** and **Flavors**.

### Stacks

In ZenML, a **stack** essentially represents a set of configurations for the infrastructure of your MLOps platform.

This is achieved by bringing together different types of **stack components**, that are responsible for specific tasks within your ML workflow. We will look at the base abstraction for the **stack components** in more detail in the next section. However, before we get there, let's first take a look at the list of all the stack component types that you can use within your **stack** in the table below:

| **Type of Stack Component**                        | **Description**                                                   |
| -------------------------------------------------- | ----------------------------------------------------------------- |
| [**Orchestrator (required)**](../extending-zenml/orchestrators.md)     | Orchestrating the runs of your pipeline                           |
| [**Artifact Store (required)**](../extending-zenml/artifact-stores.md) | Storage for the artifacts created by your pipelines               |
| [**Metadata Store (required)**](../extending-zenml/metadata-stores.md) | Tracking the execution of your pipelines/steps                    |
| [Container Registry](../extending-zenml/container-registries.md)        | Store for your containers                                         |
| [Secrets Manager](../extending-zenml/secrets-managers.md)              | Centralized location for the storage of your secrets              |
| [Step Operator](../extending-zenml/step-operators.md)                  | Execution of individual steps in specialized runtime environments |
| [Model Deployer](../extending-zenml/model-deployers.md)                | Services/platforms responsible for online model serving           |
| [Feature Store](../extending-zenml/feature-stores.md)                  | Management of your data/features                                  |
| [Experiment Tracker](../extending-zenml/experiment-trackers.md)        | Tracking your ML experiments                                      |
| [Alerter](../extending-zenml/alerters.md)                              | Sending alerts through specified channels                         |

Keep in mind that each pipeline run that you execute with ZenML will require a **stack** and each **stack** will be required to include at least an orchestrator, an artifact store, and a metadata store. The rest of the **stack components** are optional, and you can use them as you see fit.

### Base abstractions

As **stacks** represent the entire configuration of your infrastructure, **stack components** represent the configuration of individual layers within your **stack** which conduct specific self-contained tasks. For instance, each ZenML **stack** features an artifact store which is responsible for storing the artifacts generated by your pipelines, or an orchestrator which is responsible for the execution of the steps within your pipeline.

Speaking from structural standpoint, these **stack components** are built on top of base abstractions and in their core you will find the `StackComponent` class:

```python
from abc import ABC
from pydantic import BaseModel, Field
from typing import ClassVar
from uuid import UUID, uuid4

from zenml.enums import StackComponentType

class StackComponent(BaseModel, ABC):
    """Abstract class for all components of a ZenML stack."""

    # Instance configuration
    name: str
    uuid: UUID = Field(default_factory=uuid4)

    # Class parameters
    TYPE: ClassVar[StackComponentType]
    FLAVOR: ClassVar[str]

    ...
```

There are a few things to unpack here. Let's talk about Pydantic first. Pydantic is a library for [data validation and settings management](https://pydantic-docs.helpmanual.io/). Using their `BaseModel` is helping us to configure and serialize these components while allowing us to add a validation layer to each stack component instance/implementation.

You can already see how that comes into play here within the base `StackComponent` implementation. As you can see, each instance of a `StackComponent` needs to include a `name` and an auto-generated `uuid`. These variables will be tracked when we serialize the stack component object. (You can exclude an instance configuration parameter from the serialization by giving it a name which starts with `_`.)

Moreover, you can use class variables by denoting them with the `ClassVar[..]`, which are also excluded from the serialization. Each `StackComponent` implementation features two important class variables called the `TYPE` and the `FLAVOR`. The `TYPE` is utilized when we set up the base implementation for a specific type of stack component whereas the `FLAVOR` parameter is used to denote different flavors (which we will cover in the next section).

With these considerations, we can take a look at the `BaseArtifactStore` as an example:

```python
from typing import ClassVar, Set

from zenml.enums import StackComponentType
from zenml.stack import StackComponent


class BaseArtifactStore(StackComponent):
    """Abstract class for all ZenML artifact stores."""

    # Instance configuration
    path: str

    # Class parameters
    TYPE: ClassVar[StackComponentType] = StackComponentType.ARTIFACT_STORE
    SUPPORTED_SCHEMES: ClassVar[Set[str]]

    ...
```

As you can see, the `BaseArtifactStore` sets the correct `TYPE`, while introducing a new instance variable called `path` and class variable called `SUPPORTED_SCHEMES`, which will be used by all the subclasses of this base implementation.

### Flavors

Now that we have taken a look at the base abstraction of **stack components**, it is time to introduce the concept of **flavors**. In ZenML, a **flavor** represents an implementation of a specific type of **stack component** on top of its base abstraction. As an example, we can take a look at the `LocalArtifactStore`:

```python
from typing import ClassVar, Set

from zenml.artifact_stores import BaseArtifactStore


class LocalArtifactStore(BaseArtifactStore):
    """Artifact Store for local artifacts."""

    # Class configuration
    FLAVOR: ClassVar[str] = "local"
    SUPPORTED_SCHEMES: ClassVar[Set[str]] = {""}

    ...
```

As you can see from the example above, the `LocalArtifactStore` inherits from the corresponding base abstraction `BaseArtifactStore` and implements a local version. While creating this class, it is critical to set the `FLAVOR` class variable, as we will use it as a reference when we create an instance of this stack component.

Out-of-the-box, ZenML comes with a wide variety of **flavors**. These **flavors** are either built-in to the base ZenML library or enabled through the installation of specific integrations. In order to see all the available flavors for a specific type of stack component, you can use the CLI as:

```shell
zenml artifact-store flavor list
```

Through the base abstractions, ZenML also enables you to create your own flavors for any type of stack component. In order to achieve this, you can use the corresponding base abstraction, create your own implementation, and register it through the CLI:

```python
from typing import ClassVar, Set

from zenml.artifact_stores import BaseArtifactStore


class MyCustomArtifactStore(BaseArtifactStore):
    """Custom artifact store implementation."""

    # Class configuration
    FLAVOR: ClassVar[str] = "custom"
    SUPPORTED_SCHEMES: ClassVar[Set[str]] = {"custom://"}

    ...
```

followed by:

```shell
zenml artifact-store flavor register path.to.MyCustomArtifacStore
```

Once you register your new flavor, you can see it in the CLI with:

```shell
zenml artifact-store flavor list
```

### Stack components

Following the flavors, we can take a look at how we can actually create, use and manage actual **stack components** through the CLI. For this purpose, we can keep using the artifact stores as an example.

First, you can start by listing the artifact store instances. If you are using a fresh repository, you should see the default local artifact store.

```shell
zenml artifact-store list
```

Now, if you want to create a new instance of a stack component with a specific flavor, you can use the `register` command. When using this command, you need to provide a `NAME` for the instance and the required instance configuration parameters as `--param=value`.

```shell
zenml artifact-store register NAME --flavor=local --path=/path/to/your/store
```

{% hint style="info" %}
Our CLI features a wide variety of commands that let you easily manage/use your flavors. If you would like to learn more, please do: "`zenml <stack-component-type> --help`" or visit [our CLI docs](https://apidocs.zenml.io/latest/cli/).
{% endhint %}

### Bringing it together

Now that you know how to set up your stack components, let us dive into how you can use these instances to simply generate a stack:

```shell
zenml stack register STACK_NAME -o <name-of-your-orchestrator> \
                                -a <name-of-your-artifact-store> \
                                -m <name-of-your-metadata-store> \
                                ...
```

Keep in mind that any ZenML repository that you created through `zenml init` already comes with an initial active `default` stack, which features a local artifact store, a local metadata store, and a local orchestrator. You can see all of your stacks with the following command:

```shell
zenml stack list
```

As mentioned before, each pipeline run in ZenML requires an **active stack**. In order to set one of your stack as active, you can use:

```shell
zenml stack set <name-of-your-stack>
```

Once your stack is activated, you are ready to run the pipeline with the selected stack.

{% hint style="info" %}
Our CLI features a wide variety of commands that let you easily manage/use your stacks. If you would like to learn more, please do: "`zenml stack --help`" or visit [our CLI docs](https://apidocs.zenml.io/latest/cli/).
{% endhint %}

### Runtime configuration

On top of the configuration through the instance parameters, you can also provide an additional runtime configuration to the stack components for your pipeline run. In order to achieve this, you need to provide these configuration parameters as key-value pairs when you run the pipeline:

```python
pipeline.run(runtime_param_1=3, another_param='luna')
```

The provided parameters will be passed to the `prepare_pipeline_deployment` method of each stack component, and you can use this method as an entrypoint to configure your stack components even further.

### Managing the state

Through a set of properties and methods, the base interface of the `StackComponent` also allows you to control the state of your stack component:

```python
from abc import ABC
from pydantic import BaseModel


class StackComponent(BaseModel, ABC):
    """Abstract class for all components of a ZenML stack."""
    ...
    
    @property
    def is_provisioned(self) -> bool:
        """If the component provisioned resources to run."""
        return True

    @property
    def is_running(self) -> bool:
        """If the component is running."""
        return True

    def provision(self) -> None:
        """Provisions resources to run the component."""

    def deprovision(self) -> None:
        """Deprovisions all resources of the component."""
        
    def resume(self) -> None:
        """Resumes the provisioned resources of the component."""

    def suspend(self) -> None:
        """Suspends the provisioned resources of the component."""

    ...
```

By default, each stack component is assumed to be in a provisioned and running state. However, if you are dealing with a component which requires you to manage its state, you can overwrite these methods. Once your implementation is complete, you can use either:

```shell
zenml stack up
```

or

```shell
zenml artifact-store up NAME
```

to provision and resume your stack component(s) and

```shell
zenml stack down 
```

or

```shell
zenml artifact-store down NAME
```

to suspend and deprovision it.
