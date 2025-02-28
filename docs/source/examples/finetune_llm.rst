.. _basic_finetune_llm:

==========================
LLM Full Finetuning Recipe
==========================

The full fine-tune recipe updates all of the parameters of the model using supervised learning.
Given a model and a dataset comprising of input-label pairs, we train the model on these pairs using cross-entropy loss.

.. note::

  Full Fine-tuning is usually a lot more expensive that parameter-efficient techniques like LoRA, but
  can result in a higher quality model.


This recipe supports:

* :ref:`Mixed Precision Training<mp_label>`

* :ref:`Distributed Training with FSDP<dist_label>`

* :ref:`Activation Checkpointing<ac_label>`

This guide will walk you through the different aspects of the `recipe <https://github.com/pytorch/torchtune/blob/main/recipes/full_finetune.py>`_.


An example config for training the Llama 7B model using the Alpaca dataset looks something like this:

.. code-block:: yaml

    # Tokenizer
    tokenizer:
      _component_: torchtune.models.llama2.llama2_tokenizer
      path: /tmp/tokenizer.model

    # Dataset
    dataset:
      _component_: torchtune.datasets.alpaca_dataset
    shuffle: True

    # Model Arguments
    model:
      _component_: torchtune.models.llama2.llama2_7b

    checkpointer:
      _component_: torchtune.utils.FullModelMetaCheckpointer
      checkpoint_dir: /tmp/llama2
      checkpoint_files: [consolidated.00.pth]
      recipe_checkpoint: null
      output_dir: /tmp/llama2
      model_type: LLAMA2
    resume_from_checkpoint: False

    # Fine-tuning arguments
    batch_size: 2
    epochs: 3
    optimizer:
      _component_: torch.optim.SGD
      lr: 2e-5
    loss:
      _component_: torch.nn.CrossEntropyLoss
    output_dir: /tmp/alpaca-llama2-finetune

    device: cuda
    dtype: bf16

    enable_activation_checkpointing: True

To run the recipe without any changes on 4 GPUs, launch a training run using TuneCLI:

.. code-block:: bash

    tune run --nnodes 1 --nproc_per_node 4 full_finetune_distributed --config full_finetune_distributed

Dataset
-------

In this example, we use :class:`~torchtune.datasets.alpaca_dataset`
from Stanford. The following parameters are related to the data:

.. code-block:: python

    # Point the dataset to the Alpaca Dataset implementation in torchtune
    # This is set in the config
    dataset: alpaca_dataset

    # Don't mask the prompt during training
    # This is the default value
    train_on_input: True

    # Truncate after a maximum sequence length to limit memory usage
    max_seq_len: 512


.. note::
    Set ``train_on_input`` to False if you want to learn on the label only i.e. mask out the prompt. The resulting loss
    will go down a lot slower.



Model
-----

In this example, we use the `Llama 7B model <https://github.com/pytorch/torchtune/blob/main/torchtune/models/llama2.py>`_.
The following parameters are related to the model:

.. code-block:: python

    # Point the model to the default llama-7B model
    model:
      _component_: torchtune.models.llama2.llama2_7b

    checkpointer:
      _component_: torchtune.utils.FullModelMetaCheckpointer
      checkpoint_dir: /tmp/llama2
      checkpoint_files: [consolidated.00.pth]
      recipe_checkpoint: null
      output_dir: /tmp/llama2
      model_type: LLAMA2

    # Point to the default tokenizer for llama2
    tokenizer: llama2_tokenizer
    tokenizer_checkpoint: <PATH_TO_MODEL_TOKENIZER>

    # Activation checkpointing are enabled
    enable_activation_checkpointing: True


Training
--------

.. code-block:: python

    # Batch size refers to "local" batch size; global batch size is computed as
    # batch_size * num_gpus * gradient_accumulation_steps
    batch_size: 2
    lr: 2e-5
    epochs: 3

    optimizer: SGD

    epochs: 3
    loss: CrossEntropyLoss

    # default value corresponds to no accumulation
    gradient_accumulation_steps: 1

    # resume_from_checkpoint controls how the checkpoint is loaded at the beginning
    # of training; set this to True if a previously incomplete training is
    # restarting
    resume_from_checkpoint: False


.. note::
    The default optimizer is SGD instead of Adam since this uses less memory. Adam is known to result in better model
    quality.


And that's it! For more information on configs and how to update them, see this tutorial on Configs. For more information on recipes
see the tutorial on :ref:`Training Recipe Deep-Dive<recipe_deepdive>`
