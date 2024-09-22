import importlib
import os
import time
import traceback
from pydantic import ValidationError
import twmap
import argparse
from ruamel.yaml import YAML

from maps_workflow.baserule import BaseRule, BaseRuleConfig


def load_rules_from_file(file_path):
    with open(file_path, 'r') as file:
        yaml = YAML()
        return yaml.load(file)

def load_rule_from_module(rule_name):
    try:
        module = importlib.import_module(f"maps_workflow.{rule_name}")
        return module
    except ModuleNotFoundError:
        print(f"⚠️ Module 'maps_workflow.{rule_name}' not found.")
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

def execute_rules(raw_file, map_data, config):
    rule_status = {}

    def can_run_rule(rule_name):
        """Check if the rule can run based on its dependencies."""
        if rule_name not in rule_status:
            return False
        return rule_status[rule_name]

    for rule in config['rules']:
        try:
            rule = BaseRuleConfig(**rule)
        except ValidationError as e:
            print(e)
            rule_status[rule['name']] = False
            continue

        if not all(can_run_rule(dep) for dep in rule.depends_on):
            print(f"⏭️  Skipping '{rule.name}' due to unmet dependencies.")
            rule_status[rule.name] = False
            continue

        rule_module = load_rule_from_module(rule.module)
        if not rule_module:
            rule_status[rule.name] = False
            continue

        rule_func: BaseRule = getattr(rule_module, rule.class_name, None)(raw_file, map_data, rule.params)
        if not rule_func:
            print(f"⚠️ Rule function '{rule.name}' not found in module '{rule.module}'.")
            rule_status[rule.name] = False
            continue

        try:
            rule_time_started = time.time()
            violations = rule_func.evaluate()
            rule_time_finished = time.time()
            rule_time_elapsed = rule_time_finished - rule_time_started

            success = True
            if len(violations) > 0:
                success = False
                for violation in violations:
                    print(f"Violation: {violation}")

            if success:
                print(f"✅ Rule '{rule.name}' passed. ({rule_time_elapsed:.2f}s)")
                rule_status[rule.name] = True
            else:
                rule_status[rule.name] = False
                if rule.type == "require":
                    print(f"❌ Rule '{rule.name}' failed (REQUIRED). Exiting with error. ({rule_time_elapsed:.2f}s)")
                    return False
                elif rule.type == "fail":
                    print(f"⚠️ Rule '{rule.name}' failed but continuing. ({rule_time_elapsed:.2f}s)")
                elif rule.type == "skip":
                    print(f"⏭️ Rule '{rule.name}' failed but skipping. ({rule_time_elapsed:.2f}s)")

        except Exception as e:
            rule_status[rule.name] = False
            if rule.type == "require":
                print(f"❌ Rule '{rule.name}' encountered an error (REQUIRED). ({rule_time_elapsed:.2f}s) Exiting: {e}")
                return False
            elif rule.type == "fail":
                print(f"⚠️ Rule '{rule.name}' encountered an error ({rule_time_elapsed:.2f}s): {e}")
                print(traceback.print_exc())
            elif rule.type == "skip":
                print(f"⏭️ Rule '{rule.name}' encountered an error but skipping ({rule_time_elapsed:.2f}s): {e}")

    print("🎉 All rules processed successfully.")
    return True

def generate_rules_file():
    config = load_all_rules('map_rules/', exclude=[])
    rule_evaluation = []
    for rule in config['rules']:
        try:
            rule = BaseRuleConfig(**rule)
        except ValidationError as e:
            print(e)
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
    parser.add_argument("--skip")
    args = parser.parse_args()

    excluded = []
    if args.skip:
        if "," in args.skip:
            excluded = args.skip.split(",")
        else:
            excluded = [args.skip]

    config = load_all_rules('map_rules/', exclude=excluded)
    raw_file = './Aip-Gores.map'
    tw_map = twmap.Map(raw_file)
    result = execute_rules(raw_file, tw_map, config)

    if result:
        print("✅ Workflow completed successfully.")
    else:
        print("❌ Workflow failed due to required rule failure.")
