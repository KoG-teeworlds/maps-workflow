import importlib
import os
import time
import twmap
from ruamel.yaml import YAML


def load_rules_from_file(file_path):
    with open(file_path, 'r') as file:
        yaml = YAML()
        return yaml.load(file)

def load_rule_from_module(rule_name):
    try:
        module = importlib.import_module(f"rules.{rule_name}")
        return module
    except ModuleNotFoundError:
        print(f"⚠️ Module 'maps_workflow.rules.{rule_name}' not found.")
        return None

def load_all_rules(directory='rules/'):
    print(f"Loading rules from {directory}")
    all_rules = {'rules': []}
    for filename in sorted(os.listdir(directory)):
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
        rule_name = rule['name']
        rule_type = rule['type']
        r_module = rule['module']
        params = rule.get('params', {})
        dependencies = rule.get('depends_on', [])

        if not all(can_run_rule(dep) for dep in dependencies):
            print(f"⏭️  Skipping '{rule_name}' due to unmet dependencies.")
            rule_status[rule_name] = False
            continue

        # Dynamically load the corresponding rule function from the 'rules' package
        rule_module = load_rule_from_module(r_module)
        if not rule_module:
            rule_status[rule_name] = False
            continue

        # Get the rule function (assuming function name matches rule_name)
        rule_func = getattr(rule_module, r_module, None)
        if not rule_func:
            print(f"⚠️ Rule function '{rule_name}' not found in module 'rules.{r_module}'.")
            rule_status[rule_name] = False
            continue

        try:
            rule_time_started = time.time()
            violations = rule_func(raw_file, map_data, params)
            rule_time_finished = time.time()
            rule_time_elapsed = rule_time_finished - rule_time_started

            success = True
            if len(violations) > 0:
                success = False
                for violation in violations:
                    print(f"Violation: {violation}")

            if success:
                print(f"✅ Rule '{rule_name}' passed. ({rule_time_elapsed:.2f}s)")
                rule_status[rule_name] = True
            else:
                rule_status[rule_name] = False
                if rule_type == "require":
                    print(f"❌ Rule '{rule_name}' failed (REQUIRED). Exiting with error. ({rule_time_elapsed:.2f}s)")
                    return False
                elif rule_type == "fail":
                    print(f"⚠️ Rule '{rule_name}' failed but continuing. ({rule_time_elapsed:.2f}s)")
                elif rule_type == "skip":
                    print(f"⏭️ Rule '{rule_name}' failed but skipping. ({rule_time_elapsed:.2f}s)")

        except Exception as e:
            rule_status[rule_name] = False
            if rule_type == "require":
                print(f"❌ Rule '{rule_name}' encountered an error (REQUIRED). ({rule_time_elapsed:.2f}s) Exiting: {e}")
                return False  # Exit workflow with failure
            elif rule_type == "fail":
                print(f"⚠️ Rule '{rule_name}' encountered an error ({rule_time_elapsed:.2f}s): {e}")
            elif rule_type == "skip":
                print(f"⏭️ Rule '{rule_name}' encountered an error but skipping ({rule_time_elapsed:.2f}s): {e}")

    print("🎉 All rules processed successfully.")
    return True

if __name__ == '__main__':
    config = load_all_rules('map_rules/')
    raw_file = './Aip-Gores.map'
    tw_map = twmap.Map(raw_file)
    result = execute_rules(raw_file, tw_map, config)

    if result:
        print("✅ Workflow completed successfully.")
    else:
        print("❌ Workflow failed due to required rule failure.")
