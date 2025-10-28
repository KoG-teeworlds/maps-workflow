import argparse
import importlib
import logging
import os
import time
import traceback
import types
from pathlib import Path
import vote_menu_generator

import twmap
from baserule import BaseRule, BaseRuleConfig, RuleStatus, Status
from pydantic import ValidationError
from ruamel.yaml import YAML

STATUS_SYMBOL = {
    Status.COMPLETED: "✅",
    Status.FAILED: "❌",
    Status.WARN: "⚠️",
    Status.SKIP: "⏭️",
}


def load_rules_from_file(file_path: str):
    """Load rules from a YAML file."""
    with open(file_path) as file:
        yaml = YAML()
        return yaml.load(file)


def load_rule_from_module(rule_name) -> types.ModuleType | None:
    """Load a rule module by name."""
    try:
        module = importlib.import_module(f"maps_workflow.{rule_name}")
        return module
    except ModuleNotFoundError:
        logging.warning(f"⚠️ Module 'maps_workflow.{rule_name}' not found.")
        return None


def load_all_rules(directory="rules/", exclude=None):
    """Load all rules from YAML files in a directory."""
    if exclude is None:
        exclude = []

    all_rules = {"rules": []}
    for filename in sorted(os.listdir(directory)):
        if any(filename.startswith(skip) for skip in exclude):
            continue

        if filename.endswith(".yaml"):
            file_path = os.path.join(directory, filename)
            rules = load_rules_from_file(file_path)
            all_rules["rules"].extend(rules["rules"])
    return all_rules


def handle_rule_error(
    rule,
    current_rule_status,
    require_log_message: str,
    fail_log_message: str,
    skip_log_message: str,
):
    """Handle rule errors based on rule type."""
    if rule.type == "require":
        current_rule_status.status = Status.FAILED
        logging.error(require_log_message)
        newline = "\n"
        violations_text = (
            f"{newline}{newline.join([f'- {r}' for r in rule.violations])}"
            if rule.violations
            else f"{newline}- No violations detected"
        )
        result_string = (
            f"{newline}#### {STATUS_SYMBOL.get(rule.status, '❌')} {rule.rule.name}{newline}"
            f"**Explanation**: {rule.explain if rule.status != Status.COMPLETED else '-'}{newline}"
            f"**Violations**: {violations_text}"
        )
        return False, result_string
    if rule.type == "fail":
        current_rule_status.status = Status.WARN
        logging.error(fail_log_message)
        return None
    if rule.type == "skip":
        current_rule_status.status = Status.SKIP
        logging.error(skip_log_message)
        return None
    return None


def format_rule_summary(rule):
    """Format a summary for a rule."""
    newline = "\n"
    violations_text = (
        f"{newline}{newline.join([f'- {r}' for r in rule.violations])}"
        if rule.violations
        else f"{newline}- No violations detected"
    )
    return (
        f"{newline}#### {STATUS_SYMBOL.get(rule.status, '❌')} {rule.rule.name}{newline}"
        f"**Explanation**: {rule.explain if rule.status != Status.COMPLETED else '-'}{newline}"
        f"**Violations**: {violations_text}"
    )


def _process_single_rule(rule_config, rule_status, raw_file, map_data):
    """Process a single rule configuration."""
    current_rule_status = RuleStatus(explain=None, status=Status.FAILED, violations=[])
    try:
        rule = BaseRuleConfig(**rule_config)
    except ValidationError as validation_error:
        logging.error(validation_error)
        return None

    rule_status[rule.name] = current_rule_status
    current_rule_status.rule = rule

    # Check dependencies
    def can_run_rule(rule_name):
        return rule_name in rule_status and rule_status[rule_name]

    if not all(can_run_rule(dep) for dep in rule.depends_on):
        logging.info(f"⏭️  Skipping '{rule.name}' due to unmet dependencies.")
        current_rule_status.passed = Status.FAILED
        return None

    # Load rule module
    rule_module = load_rule_from_module(rule.module)
    if not rule_module:
        current_rule_status.passed = Status.FAILED
        return None

    rule_func: BaseRule | None = getattr(rule_module, rule.class_name, None)(raw_file, map_data, rule.params)
    if rule_func is None:
        logging.warning(f"⚠️ Rule function '{rule.name}' not found in module '{rule.module}'.")
        current_rule_status.passed = Status.WARN
        return None

    return _execute_single_rule(rule, rule_func, current_rule_status)


def _execute_single_rule(rule, rule_func, current_rule_status):
    """Execute a single rule and handle its result."""
    current_rule_status.explain = rule_func.explain()
    rule_time_started = time.time()

    try:
        violations = rule_func.evaluate()
        rule_time_elapsed = time.time() - rule_time_started

        if violations:
            current_rule_status.violations = violations
            for violation in violations:
                logging.info(f"Violation: {violation}")

            return handle_rule_error(
                rule,
                current_rule_status,
                f"❌ Rule '{rule.name}' failed (REQUIRED). Exiting with error. ({rule_time_elapsed:.2f}s)",
                f"⚠️ Rule '{rule.name}' failed but continuing. ({rule_time_elapsed:.2f}s)",
                f"⏭️ Rule '{rule.name}' failed but skipping. ({rule_time_elapsed:.2f}s)",
            )
        else:
            logging.info(f"✅ Rule '{rule.name}' passed. ({rule_time_elapsed:.2f}s)")
            current_rule_status.status = Status.COMPLETED

    except Exception as exception:
        rule_time_elapsed = time.time() - rule_time_started
        error_msg = f"❌ Rule '{rule.name}' encountered an error (REQUIRED). ({rule_time_elapsed:.2f}s)"
        return handle_rule_error(
            rule,
            current_rule_status,
            f"{error_msg} Exiting: {exception}",
            f"⚠️ Rule '{rule.name}' encountered an error ({rule_time_elapsed:.2f}s): {traceback.print_exc()}",
            f"⏭️ Rule '{rule.name}' encountered an error but skipping ({rule_time_elapsed:.2f}s): {exception}",
        )
    return None


def execute_rules(raw_file, map_data, config) -> tuple[bool, str]:
    """Execute all rules and return success status and summary."""
    rule_status: dict[str, RuleStatus] = {}

    for rule_config in config["rules"]:
        result = _process_single_rule(rule_config, rule_status, raw_file, map_data)
        if result is not None:
            return result

    result_string = "".join(format_rule_summary(rule_status[passed]) for passed in rule_status)
    logging.info("🎉 All rules processed successfully.")
    return True, result_string


def generate_rules_file():
    """Generate a list of all available rules with their descriptions."""
    config = load_all_rules("map_rules/", exclude=[])
    rule_evaluation = []
    for rule_config in config["rules"]:
        try:
            rule = BaseRuleConfig(**rule_config)
        except ValidationError as validation_error:
            logging.error(validation_error)
            continue

        rule_module = load_rule_from_module(rule.module)
        if not rule_module:
            continue

        rule_func: BaseRule = getattr(rule_module, rule.class_name, None)(None, None, rule.params)
        if not rule_func:
            continue

        rule_evaluation.append(
            {
                "name": rule.name,
                "desc": rule.description,
                "explain": rule_func.explain(),
                "required": rule.type == "require",
            }
        )
    return rule_evaluation


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--map", default=os.environ.get("INPUT_MAP"))
    parser.add_argument("--skip")
    parser.add_argument("--ci", action="store_true")
    parser.add_argument("--action", default=os.environ.get("ACTION", "check"))
    parser.add_argument("--mapscsv")
    args = parser.parse_args()

    output = []
    exit_code = 0

    try:
        if args.action == "check":
            file_path = Path(args.map)
            excluded = []
            if args.skip:
                excluded = args.skip.split(",") if "," in args.skip else [args.skip]

            config = load_all_rules("map_rules/", exclude=excluded)
            tw_map = twmap.Map(args.map)
            result = execute_rules(args.map, tw_map, config)

            if args.ci:
                output.append(f"## Output for map `{file_path.name}`")
                output.append(f"### Rules\n{result[1]}")

            if result[0]:
                output.append("✅ Workflow completed successfully.")
            else:
                output.append("❌ Workflow failed due to required rule failure.")
                exit_code = 1

        elif args.action == "generate_votes":
            output.append("Generating votes... please wait")
            vote_menu_generator.generate_votes()
        elif args.action == "check_if_vote_exists":
            output.append(f"Reading {args.mapscsv} ...")
        else:
            output.append("❌ Invalid action defined!")
            exit_code = 1
    except Exception:
        exit_code = 1
    finally:
        for line in output:
            print(line)
