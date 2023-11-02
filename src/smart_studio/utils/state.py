import configparser
import logging
import json
import os
import yaml
logger = logging.getLogger()

from appdirs import user_data_dir

appname = "SmartStudio"
appauthor = "Yale Hartmann"
path_to_settings = os.path.join(user_data_dir(appname, appauthor), 'settings.ini')
path_to_state = os.path.join(user_data_dir(appname, appauthor), 'state.yml')
path_to_log_smart = os.path.join(user_data_dir(appname, appauthor), 'smart_studio.log')
path_to_log_ln = os.path.join(user_data_dir(appname, appauthor), 'livenodes.log')

os.makedirs(user_data_dir(appname, appauthor), exist_ok=True)

logger.info(f'Using settings file {path_to_settings}')
logger.info(f'Using state file {path_to_state}')
logger.info(f'Using log files {path_to_log_smart}, {path_to_log_ln}')

# === Settings ==============================================================================
SETTINGS = configparser.ConfigParser()
try:
    SETTINGS.read(path_to_settings)
except:
    logger.exception(f'Could not open settings. Creating new ({path_to_settings})')

def write_settings():
    with open(path_to_settings, 'w') as f:
        SETTINGS.write(f)

def settings_parse(json_str):
    return json.loads(json_str)

# === State ==============================================================================
if not os.path.exists(path_to_state):
    logger.info(f'Creating new state file ({path_to_state})')
    with open(path_to_state, 'w') as f:
        yaml.dump({}, f)

with open(path_to_state, 'r') as file:
    STATE = yaml.safe_load(file)

def write_state():
    with open(path_to_state, 'w') as f:
        yaml.dump(STATE, f)


# === LOG ==============================================================================
import logging 

logger_smart = logging.getLogger("smart-studio")
logger_smart_file_handler = logging.FileHandler(path_to_log_smart, mode='w')
logger_smart_file_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(processName)s | %(threadName)s | %(message)s')
logger_smart_file_handler.setFormatter(formatter)
logger_smart.addHandler(logger_smart_file_handler)

logger_ln = logging.getLogger("livenodes")
logger_ln_file_handler = logging.FileHandler(path_to_log_ln, mode='w')
logger_ln_file_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(processName)s | %(threadName)s | %(message)s')
logger_ln_file_handler.setFormatter(formatter)
logger_ln.addHandler(logger_ln_file_handler)