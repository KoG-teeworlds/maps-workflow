import importlib
import os
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
    for filename in os.listdir(directory):
        if filename.endswith('.yaml'):
            file_path = os.path.join(directory, filename)
            rules = load_rules_from_file(file_path)
            all_rules['rules'].extend(rules['rules'])
    return all_rules

def execute_rules(map_data, config):
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

        # Check if dependencies are satisfied
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
            success = rule_func(map_data, params)

            if success:
                print(f"✅ Rule '{rule_name}' passed.")
                rule_status[rule_name] = True
            else:
                rule_status[rule_name] = False
                if rule_type == "require":
                    print(f"❌ Rule '{rule_name}' failed (REQUIRED). Exiting with error.")
                    return False  # Exit workflow with failure
                elif rule_type == "fail":
                    print(f"⚠️ Rule '{rule_name}' failed but continuing...")
                elif rule_type == "skip":
                    print(f"⏭️ Rule '{rule_name}' failed but skipping.")

        except Exception as e:
            rule_status[rule_name] = False
            if rule_type == "require":
                print(f"❌ Rule '{rule_name}' encountered an error (REQUIRED). Exiting: {e}")
                return False  # Exit workflow with failure
            elif rule_type == "fail":
                print(f"⚠️ Rule '{rule_name}' encountered an error: {e}")
            elif rule_type == "skip":
                print(f"⏭️ Rule '{rule_name}' encountered an error but skipping: {e}")

    print("🎉 All rules processed successfully.")
    return True

if __name__ == '__main__':
    config = load_all_rules('map_rules/')
    tw_map = twmap.Map('./Aip-Gores.map')
    result = execute_rules(tw_map, config)

    if result:
        print("✅ Workflow completed successfully.")
    else:
        print("❌ Workflow failed due to required rule failure.")
