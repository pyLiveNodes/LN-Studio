import json
import logging
import os
import glob
logger = logging.getLogger()

from smart_studio.utils.state import STATE, write_state

def migrate():
    home_dir = os.getcwd()
    if os.path.exists(os.path.join(home_dir, 'smart-state.json')):
        logger.info('Migrating Smart State')
        
        with open(os.path.join(home_dir, 'smart-state.json'), 'r') as f:
            old_state = json.load(f)
        
        STATE['Window'] = {
            'size': old_state['values']['window_size'],
        }

        STATE['View.Home'] = {
            'selected_folder': os.path.abspath(os.path.join(home_dir, old_state['spaces']['views']['values']['Home']['cur_project'], 'pipelines')),
            'selected_file': old_state['spaces']['views']['values']['Home']['cur_pipeline'].split('/')[-1].replace('.json', ''),
            'folders': [f"{f}/pipelines" for f in glob.glob(os.path.abspath(os.path.join(home_dir, old_state['values']['projects']))) if os.path.isdir(os.path.abspath(f))]
        }

        write_state()
        # os.remove(os.path.join(home_dir, 'smart-state.json'))