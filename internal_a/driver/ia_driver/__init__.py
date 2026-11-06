"""Internal-A local native-calling driver (DRAFT). Evidence packager: it never decides PASS.

SPDX-License-Identifier: Apache-2.0

Modes: STUB_TEST (locally defined stubs/mocks only) and SUBJECT (pinned native components;
disabled by default, requires a separate explicit execution authorization record).
The parent process never imports a subject component; native calls run in a fresh child interpreter.
"""
DRIVER_VERSION = "internal-a-driver/1.0.0-draft"
BUNDLE_SCHEMA = "ia-observation-bundle/1"          # the merged evaluator's declared schema (ia_eval.engine.BUNDLE_SCHEMA)
CHILD_SPEC_SCHEMA = "ia-driver-child-spec/1"
CHILD_RESULT_SCHEMA = "ia-driver-child-result/1"
MODES = ("STUB_TEST", "SUBJECT")
