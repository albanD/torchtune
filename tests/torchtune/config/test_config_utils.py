# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

from unittest import mock

import pytest
from torchtune.config._utils import (
    _get_chat_format,
    _get_component_from_path,
    _get_instruct_template,
    _merge_yaml_and_cli_args,
    _try_get_component,
    InstantiationError,
)
from torchtune.data import AlpacaInstructTemplate, Llama2ChatFormat
from torchtune.utils.argparse import TuneRecipeArgumentParser

_CONFIG = {
    "a": 1,
    "b": {
        "_component_": 2,
        "c": 3,
    },
    "d": 4,
}


class TestUtils:
    def test_get_component_from_path(self):
        good_paths = [
            "torchtune",  # Test single module without dot
            "torchtune.models",  # Test dotpath for a module
            "torchtune.models.llama2.llama2_7b",  # Test dotpath for an object
        ]
        for path in good_paths:
            _ = _get_component_from_path(path)

        # Test that a relative path fails
        with pytest.raises(ValueError, match="Relative imports are not supported"):
            _ = _get_component_from_path(".test")
        # Test that a non-existent path fails
        with pytest.raises(
            InstantiationError, match="Error loading 'torchtune.models.dummy'"
        ):
            _ = _get_component_from_path("torchtune.models.dummy")

    @mock.patch("torchtune.utils.argparse.OmegaConf.load", return_value=_CONFIG)
    def test_merge_yaml_and_cli_args(self, mock_load):
        parser = TuneRecipeArgumentParser("test parser")
        yaml_args, cli_args = parser.parse_known_args(
            [
                "--config",
                "test.yaml",
                "b.c=4",  # Test overriding a flat param in a component
                "b=5",  # Test overriding component path
                "b.b.c=6",  # Test nested dotpath
                "d=6",  # Test overriding a flat param
                "e=7",  # Test adding a new param
            ]
        )
        conf = _merge_yaml_and_cli_args(yaml_args, cli_args)
        assert conf.a == 1, f"a == {conf.a}, not 1 as set in the config."
        assert (
            conf.b._component_ == 5
        ), f"b == {conf.b._component_}, not 5 as set in overrides."
        assert conf.b.c == 4, f"b.c == {conf.b.c}, not 4 as set in overrides."
        assert conf.b.b.c == 6, f"b.b.c == {conf.b.b.c}, not 6 as set in overrides."
        assert conf.d == 6, f"d == {conf.d}, not 6 as set in overrides."
        assert conf.e == 7, f"e == {conf.e}, not 7 as set in overrides."
        mock_load.assert_called_once()

        yaml_args, cli_args = parser.parse_known_args(
            [
                "--config",
                "test.yaml",
                "b=5",  # Test overriding component path but keeping other kwargs
            ]
        )
        conf = _merge_yaml_and_cli_args(yaml_args, cli_args)
        assert (
            conf.b._component_ == 5
        ), f"b == {conf.b._component_}, not 5 as set in overrides."
        assert conf.b.c == 3, f"b.c == {conf.b.c}, not 3 as set in the config."
        assert mock_load.call_count == 2

        yaml_args, cli_args = parser.parse_known_args(
            [
                "--config",
                "test.yaml",
                "b.c=5",  # Test overriding kwarg but keeping component path
            ]
        )
        conf = _merge_yaml_and_cli_args(yaml_args, cli_args)
        assert (
            conf.b._component_ == 2
        ), f"b == {conf.b._component_}, not 2 as set in the config."
        assert conf.b.c == 5, f"b.c == {conf.b.c}, not 5 as set in overrides."
        assert mock_load.call_count == 3

        yaml_args, cli_args = parser.parse_known_args(
            [
                "--config",
                "test.yaml",
                "b",  # Test invalid override
            ]
        )
        with pytest.raises(
            ValueError, match="Command-line overrides must be in the form of key=value"
        ):
            _ = _merge_yaml_and_cli_args(yaml_args, cli_args)

    def test_try_get_component(self):
        # Test a valid classname
        template = _try_get_component(
            module_path="torchtune.data._instruct_templates",
            component_name="AlpacaInstructTemplate",
            class_type="InstructTemplate",
        )
        assert template == AlpacaInstructTemplate

        # Test an invalid class
        with pytest.raises(
            ValueError,
            match="Invalid InstructTemplate class",
        ):
            _ = _try_get_component(
                module_path="torchtune.data._instruct_templates",
                component_name="InvalidTemplate",
                class_type="InstructTemplate",
            )

    def test_get_instruct_template(self):
        assert (
            _get_instruct_template("AlpacaInstructTemplate") == AlpacaInstructTemplate
        )

    def test_get_chat_format(self):
        assert _get_chat_format("Llama2ChatFormat") == Llama2ChatFormat
