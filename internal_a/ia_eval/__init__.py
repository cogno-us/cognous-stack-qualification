"""Internal Milestone A (Q-A) assessment evaluator -- stdlib only, read-only, no-effect.

SPDX-License-Identifier: Apache-2.0

This package judges *observation bundles* against a source-derived oracle. It never
imports, executes or calls a subject component, and it never reads developer
checker verdicts as evidence. See internal_a/README.md.
"""
EVALUATOR_VERSION = "internal-a-evaluator/1.0.0-draft"
