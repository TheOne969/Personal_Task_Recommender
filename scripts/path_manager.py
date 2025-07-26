import os
from pathlib import Path
from dotenv import load_dotenv

class PathManager:
    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        # Directory paths
        self.data_dir = Path(os.getenv('DATA_DIR'))
        self.scripts_dir = Path(os.getenv('SCRIPTS_DIR'))
        self.ui_dir = Path(os.getenv('UI_DIR'))
        self.configs_dir = Path(os.getenv('CONFIGS_DIR'))
        
        # Config files
        self.config_file = Path(os.getenv('CONFIG_FILE'))
        self.goals_file = Path(os.getenv('GOALS_FILE'))
        self.tasks_file = Path(os.getenv('TASKS_FILE'))
        self.category_mapping_file = Path(os.getenv('CATEGORY_MAPPING_FILE'))
        

# Create singleton instance which will be used by all whoever imports it. Also saves time of making instances.
paths = PathManager()
