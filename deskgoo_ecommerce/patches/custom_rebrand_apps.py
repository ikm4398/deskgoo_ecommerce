import importlib

# Map of apps and their new titles
apps_to_override = {
    "frappe": "Deskgoo Framework",
    "healthcare": "Deskgoo Healthcare",
    "hrms": "Deskgoo HR",
    "erpnext": "Deskgoo ERP"
}

def override_hook_titles():
    for app, title in apps_to_override.items():
        try:
            module = importlib.import_module(f"{app}.hooks")
        except ModuleNotFoundError:
            continue  # skip if app is not installed

        # Override app_title
        module.app_title = title

        # Override add_to_apps_screen title if exists
        if hasattr(module, "add_to_apps_screen") and module.add_to_apps_screen:
            module.add_to_apps_screen[0]["title"] = title