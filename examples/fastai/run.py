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

from fastai.data.core import DataLoaders
from fastai.learner import Learner
from fastai.vision.all import *
from huggingface_hub import from_pretrained_fastai

from zenml.integrations.fastai.materializers.fastai_learner_materializer import (
    FastaiLearnerMaterializer,
)
from zenml.pipelines import pipeline
from zenml.steps import step

CAT_IMAGES_PATH = "data/images/"


@step
def data_importer() -> DataLoaders:
    data_block = DataBlock(
        blocks=(ImageBlock, CategoryBlock),
        get_items=get_image_files,
        splitter=RandomSubsetSplitter(train_sz=0, val_sz=1),
        item_tfms=Resize(224),
    )
    return data_block.dataloaders(CAT_IMAGES_PATH, bs=8)


@step
def model_importer() -> Learner:
    return from_pretrained_fastai("strickvl/redaction-classifier-fastai")


# @step
# def fine_tune_model(data, model: Learner) -> Learner:
#     pass


# @pipeline
# def fastai_pipeline(data_importer, model_importer, fine_tune_model):
#     data = data_importer()
#     model = model_importer()
#     fine_tune_model(data, model)


@pipeline
def test_pipeline(model_importer):
    model_importer()


if __name__ == "__main__":
    test = test_pipeline(
        model_importer().with_return_materializers(FastaiLearnerMaterializer)
    )
    test.run()