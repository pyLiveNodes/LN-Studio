import json
import logging
import os
import glob
import shutil
import sys
from livenodes import Node
logger = logging.getLogger()
logger.setLevel(logging.INFO)

from ln_studio.utils.state import write_state, STATE

def migrate():
    logger_stdout_handler = logging.StreamHandler(sys.stdout)
    logger_stdout_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(name)s | %(levelname)s | %(message)s')
    logger_stdout_handler.setFormatter(formatter)
    logger.addHandler(logger_stdout_handler)

    home_dir = os.getcwd()
    logger.info(f'Migrating from cwd: {home_dir}')


    if os.path.exists(os.path.join(home_dir, 'smart-state.json')):
        # === Migrate old state ================================================================
        logger.info('Migrating Smart State')

        with open(os.path.join(home_dir, 'smart-state.json'), 'r') as f:
            old_state = json.load(f)
            logger.info('Old State:')
            logger.info(old_state)

        if 'Window' not in STATE:
            STATE['Window'] = {
                'size': old_state['values']['window_size']
            }

        folders = [f for f in glob.glob(os.path.abspath(os.path.join(home_dir, old_state['values']['projects']))) if os.path.isdir(os.path.abspath(f))]
        if 'View.Home' not in STATE:
            STATE['View.Home'] = {
                'selected_folder': os.path.abspath(os.path.join(home_dir, old_state['spaces']['views']['values']['Home']['cur_project'])),
                'selected_file': os.path.abspath(os.path.join(home_dir, old_state['spaces']['views']['values']['Home']['cur_pipeline'].replace('/pipelines/', '/'))),
                'folders': []
            }

        STATE['View.Home']['folders'].extend(folders)

        write_state()

        # === Migrate pipelines ================================================================
        logger.info('Migrating Pipelines')
        for folder in folders:
            files = glob.glob(f"{folder}/pipelines/*.json")
            for f in files:
                logger.info(f"=== Parsing: {f} ===================================")
                pipeline = Node.load(f, ignore_connection_errors=False)
                logger.info('loaded')
                logger.info(f'Removing: {f}')
                os.remove(f)

                f_short = f.replace('.json', '')
                if os.path.exists(f"{f_short}"):
                    # remove digraph files
                    logger.info('removed digraph file')
                    os.remove(f"{f_short}")

                # save pipeline as yml and with images
                f_new = f_short.replace('/pipelines/', '/')
                pipeline.save(f_new, extension='yml')
                logger.info('saved condensed new')
                pipeline.dot_graph_full(transparent_bg=True, filename=f_new, file_type='pdf')
                pipeline.dot_graph_full(transparent_bg=True, filename=f_new, file_type='png', edge_labels=False)
                logger.info('created images')

                # move gui files
                gui_short = f_short.replace('/pipelines/', '/gui/')
                if os.path.exists(f"{gui_short}.json"):
                    os.rename(f"{gui_short}.json", f"{f_new}_gui.json")
                    logger.info(f"renamed: {gui_short}.json")
                if os.path.exists(f"{gui_short}_dock.xml"):
                    os.rename(f"{gui_short}_dock.xml", f"{f_new}_gui_dock.xml")
                    logger.info(f"renamed: {gui_short}_dock.xml")
                if os.path.exists(f"{gui_short}_dock_debug.xml"):
                    os.rename(f"{gui_short}_dock_debug.xml", f"{f_new}_gui_dock_debug.xml")
                    logger.info(f"renamed: {gui_short}_dock_debug.xml")

            # remove old folders
            logger.info(f'Removing: {os.path.dirname(f_short)}')
            shutil.rmtree(os.path.dirname(f_short))
            logger.info(f'Removing: {os.path.dirname(gui_short)}')
            shutil.rmtree(os.path.dirname(gui_short), ignore_errors=True)
            log_short = f_short.replace('/pipelines/', '/logs/')
            logger.info(f'Removing: {os.path.dirname(log_short)}')
            shutil.rmtree(os.path.dirname(log_short), ignore_errors=True)

        # === Clean old files ================================================================
        logger.info(f'Removing: smart-state.json')
        os.remove(os.path.join(home_dir, 'smart-state.json'))
        if os.path.exists(os.path.join(home_dir, 'ln_studio.log')):
            logger.info(f'Removing: ln_studio.log')
            os.remove(os.path.join(home_dir, 'ln_studio.log'))
        if os.path.exists(os.path.join(home_dir, 'ln_studio.full.log')):
            logger.info(f'Removing: ln_studio.full.log')
            os.remove(os.path.join(home_dir, 'ln_studio.full.log'))

        logger.info(f'Finished')
