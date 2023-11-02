import json
import logging
import os
import glob
import shutil
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

        folders = [f for f in glob.glob(os.path.abspath(os.path.join(home_dir, old_state['values']['projects']))) if os.path.isdir(os.path.abspath(f))]
        STATE['View.Home'] = {
            'selected_folder': os.path.abspath(os.path.join(home_dir, old_state['spaces']['views']['values']['Home']['cur_project'])),
            'selected_file': os.path.abspath(os.path.join(home_dir, old_state['spaces']['views']['values']['Home']['cur_pipeline'].replace('/pipelines/', '/'))),
            'folders': folders
        }

        write_state()
        
        # === Migrate pipelines ================================================================
        logger.info('Migrating Pipelines')
        for folder in folders:
            files = glob.glob(f"{folder}/pipelines/*.json")
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
                gui_short = f_short.replace('/pipelines/', '/gui/')
                if os.path.exists(f"{gui_short}.json"):
                    os.rename(f"{gui_short}.json", f"{f_new}_gui.json")
                if os.path.exists(f"{gui_short}_dock.xml"):
                    os.rename(f"{gui_short}_dock.xml", f"{f_new}_gui_dock.xml")
                if os.path.exists(f"{gui_short}_dock_debug.xml"):
                    os.rename(f"{gui_short}_dock_debug.xml", f"{f_new}_gui_dock_debug.xml")
            
            # remove old folders
            shutil.rmtree(os.path.dirname(f_short))
            shutil.rmtree(os.path.dirname(gui_short), ignore_errors=True)
            shutil.rmtree(os.path.dirname(f_short.replace('/pipelines/', '/logs/')), ignore_errors=True)

        # === Clean old files ================================================================
        os.remove(os.path.join(home_dir, 'smart-state.json'))
        if os.path.exists(os.path.join(home_dir, 'smart_studio.log')):
            os.remove(os.path.join(home_dir, 'smart_studio.log'))
        if os.path.exists(os.path.join(home_dir, 'smart_studio.full.log')):
            os.remove(os.path.join(home_dir, 'smart_studio.full.log'))

