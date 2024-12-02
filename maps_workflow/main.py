import importlib
import os
from pathlib import Path
import sys
import time
import traceback
import logging
from pydantic import ValidationError
import twmap
import argparse
from ruamel.yaml import YAML
import csv
import types

from maps_workflow.baserule import BaseRule, BaseRuleConfig, RuleStatus, Status


def load_rules_from_file(file_path):
    with open(file_path, 'r') as file:
        yaml = YAML()
        return yaml.load(file)

def load_rule_from_module(rule_name) -> types.ModuleType | None:
    try:
        module = importlib.import_module(f"maps_workflow.{rule_name}")
        return module
    except ModuleNotFoundError:
        logging.warning(f"⚠️ Module 'maps_workflow.{rule_name}' not found.")
        return None

def load_all_rules(directory='rules/', exclude=[]):
    all_rules = {'rules': []}
    for filename in sorted(os.listdir(directory)):
        if any(filename.startswith(skip) for skip in exclude):
            continue

        if filename.endswith('.yaml'):
            file_path = os.path.join(directory, filename)
            rules = load_rules_from_file(file_path)
            all_rules['rules'].extend(rules['rules'])
    return all_rules

def execute_rules(raw_file, map_data, config) -> tuple[bool, str]:
    rule_status: dict[str, RuleStatus] = {}

    def can_run_rule(rule_name):
        """Check if the rule can run based on its dependencies."""
        if rule_name not in rule_status:
            return False
        return rule_status[rule_name]

    for rule in config['rules']:
        current_rule_status = RuleStatus(explain=None, status=Status.FAILED, violations=[])
        try:
            rule = BaseRuleConfig(**rule)
        except ValidationError as e:
            logging.error(e)
            rule = BaseRuleConfig({'name': rule['name']})
            continue

        rule_status[rule.name] = current_rule_status
        current_rule_status.rule = rule

        if not all(can_run_rule(dep) for dep in rule.depends_on):
            logging.info(f"⏭️  Skipping '{rule.name}' due to unmet dependencies.")
            current_rule_status.passed = Status.FAILED
            continue

        rule_module = load_rule_from_module(rule.module)
        if not rule_module:
            current_rule_status.passed = Status.FAILED
            continue

        rule_func: BaseRule|None = getattr(rule_module, rule.class_name, None)(raw_file, map_data, rule.params)
        if not rule_func:
            logging.warning(f"⚠️ Rule function '{rule.name}' not found in module '{rule.module}'.")
            current_rule_status.passed = Status.WARN
            continue

        current_rule_status.explain = rule_func.explain()

        rule_time_started = time.time()
        try:
            violations = rule_func.evaluate()
            rule_time_finished = time.time()
            rule_time_elapsed: float = rule_time_finished - rule_time_started

            success = True
            if len(violations) > 0:
                success = False
                current_rule_status.violations = violations
                for violation in violations:
                    logging.info(f"Violation: {violation}")

            if success:
                logging.info(f"✅ Rule '{rule.name}' passed. ({rule_time_elapsed:.2f}s)")
                current_rule_status.status = Status.COMPLETED
            else:
                if rule.type == "require":
                    current_rule_status.status = Status.FAILED
                    logging.error(f"❌ Rule '{rule.name}' failed (REQUIRED). Exiting with error. ({rule_time_elapsed:.2f}s)")
                    status_symbol = {
                        Status.COMPLETED: "✅",
                        Status.FAILED: "❌",
                        Status.WARN: "⚠️",
                        Status.SKIP: "⏭️"
                    }
                    result_string = (
                    f"\n#### { status_symbol.get(rule.status, '❌') } {rule.rule.name}\n"
                    f"**Explanation**: { rule.explain if rule.status != Status.COMPLETED else '-' }\n"
                    f"**Violations**: { "\n" if len(rule.violations) > 0 else "\n- No violations detected" }\n"
                    f"{ "\n".join([f"- {r}" for r in rule.violations]) }"
                    )
                    return False, result_string
                elif rule.type == "fail":
                    current_rule_status.status = Status.WARN
                    logging.info(f"⚠️ Rule '{rule.name}' failed but continuing. ({rule_time_elapsed:.2f}s)")
                elif rule.type == "skip":
                    current_rule_status.status = Status.SKIP
                    logging.info(f"⏭️ Rule '{rule.name}' failed but skipping. ({rule_time_elapsed:.2f}s)")

        except Exception as e:
            rule_time_finished = time.time()
            rule_time_elapsed: float = rule_time_finished - rule_time_started
            if rule.type == "require":
                current_rule_status.status = Status.FAILED
                logging.error(f"❌ Rule '{rule.name}' encountered an error (REQUIRED). ({rule_time_elapsed:.2f}s) Exiting: {e}")
                status_symbol = {
                    Status.COMPLETED: "✅",
                    Status.FAILED: "❌",
                    Status.WARN: "⚠️",
                    Status.SKIP: "⏭️"
                }
                result_string = (
                f"\n#### { status_symbol.get(rule.status, '❌') } {rule.rule.name}\n"
                f"**Explanation**: { rule.explain if rule.status != Status.COMPLETED else '-' }\n"
                f"**Violations**: { "\n" if len(rule.violations) > 0 else "\n- No violations detected" }\n"
                f"{ "\n".join([f"- {r}" for r in rule.violations]) }"
                )
                return False, result_string
            elif rule.type == "fail":
                current_rule_status.status = Status.WARN
                logging.error(f"⚠️ Rule '{rule.name}' encountered an error ({rule_time_elapsed:.2f}s): {traceback.print_exc()}")
            elif rule.type == "skip":
                current_rule_status.status = Status.SKIP
                logging.error(f"⏭️ Rule '{rule.name}' encountered an error but skipping ({rule_time_elapsed:.2f}s): {e}")

    result_string = ""
    for passed in rule_status:
        rule = rule_status[passed]
        status_symbol = {
            Status.COMPLETED: "✅",
            Status.FAILED: "❌",
            Status.WARN: "⚠️",
            Status.SKIP: "⏭️"
        }
        result_string += (
        f"\n#### { status_symbol.get(rule.status, '❌') } {rule.rule.name}\n"
        f"**Explanation**: { rule.explain if rule.status != Status.COMPLETED else '-' }\n"
        f"**Violations**: { "\n" if len(rule.violations) > 0 else "\n- No violations detected" }\n"
        f"{ "\n".join([f"- {r}" for r in rule.violations]) }"
        )

    logging.info("🎉 All rules processed successfully.")
    return True, result_string

def generate_rules_file():
    config = load_all_rules('map_rules/', exclude=[])
    rule_evaluation = []
    for rule in config['rules']:
        try:
            rule = BaseRuleConfig(**rule)
        except ValidationError as e:
            logging.error(e)
            continue

        rule_module = load_rule_from_module(rule.module)
        if not rule_module:
            continue

        rule_func: BaseRule = getattr(rule_module, rule.class_name, None)(None, None, rule.params)
        if not rule_func:
            continue

        rule_evaluation.append({ 'name': rule.name, 'desc': rule.description, 'explain': rule_func.explain(), 'required': True if rule.type == 'require' else False })
    return rule_evaluation


if __name__ == '__main__':
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

            config = load_all_rules('map_rules/', exclude=excluded)
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
        elif args.action == "check_if_vote_exists":
            output.append(f"Reading {args.mapscsv} ...")
        else:
            output.append("❌ Invalid action defined!")
            exit_code = 1
    except Exception as e:
        exit_code = 1
    finally:
        for line in output:
            print(line)
