app_name = "deskgoo_ecommerce"
app_title = "Deskgoo Ecommerce"
app_publisher = "Deskgoo"
app_description = "D"
app_email = "ikm4398@gmail.com"
app_license = "mit"

# Apps
# ------------------
import importlib

# Custom Re-Branding Apps
try:
    override_module = importlib.import_module(f"{app_name}.patches.custom_rebrand_apps")
    override_module.override_hook_titles()
except ModuleNotFoundError:
    pass
