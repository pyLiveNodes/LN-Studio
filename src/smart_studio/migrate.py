import json
import logging
import os
import glob
from livenodes import Node
logger = logging.getLogger()

from smart_studio.utils.state import write_state, STATE

def migrate():
    home_dir = os.getcwd()

    if os.path.exists(os.path.join(home_dir, 'smart-state.json')):
        # === Migrate old state ================================================================
        logger.info('Migrating Smart State')
        
        with open(os.path.join(home_dir, 'smart-state.json'), 'r') as f:
            old_state = json.load(f)
        
        STATE['Window'] = {
            'size': old_state['values']['window_size'],
        }

        folders = [f"{f}/pipelines" for f in glob.glob(os.path.abspath(os.path.join(home_dir, old_state['values']['projects']))) if os.path.isdir(os.path.abspath(f))]
        STATE['View.Home'] = {
            'selected_folder': os.path.abspath(home_dir, old_state['spaces']['views']['values']['Home']['selected_folder']),
            'selected_file': os.path.abspath(home_dir, old_state['spaces']['views']['values']['Home']['selected_file'].replace('/pipelines/', '/')),
            'folders': folders
        }

        write_state()
        
        # === Migrate pipelines ================================================================
        logger.info('Migrating Pipelines')
        for folder in folders:
            files = glob.glob(os.path.join(folder, '*.json'))
            for f in files:
                pipeline = Node.load(f, ignore_connection_errors=False)
                os.remove(f)

                f_short = f.replace('.json', '')
                if os.path.exists(f"{f_short}"):
                    # remove digraph files
                    os.remove(f"{f_short}")

                # save pipeline as yml and with images
                f_new = f_short.replace('/pipelines/', '/')
                pipeline.save(f_new, extension='yml')
                pipeline.dot_graph_full(transparent_bg=True, filename=f_new, file_type='pdf')
                pipeline.dot_graph_full(transparent_bg=True, filename=f_new, file_type='png')

                # move gui files
                gui_short = f'f"{f_new}/gui/'
                if os.path.exists(f"{gui_short}.json"):
                    os.rename(f"{gui_short}.json", f"{f_new}_gui.json")
                if os.path.exists(f"{gui_short}_dock.xml"):
                    os.rename(f"{gui_short}_dock.xml", f"{f_new}_gui_dock.xml")
                if os.path.exists(f"{gui_short}_dock_debug.xml"):
                    os.rename(f"{gui_short}_dock_debug.xml", f"{f_new}_gui_dock_debug.xml")
            
            os.remove(os.path.dirname(gui_short))
            os.remove(os.path.dirname(f"{f_new}/logs/"))

        os.remove(os.path.join(home_dir, 'smart-state.json'))

