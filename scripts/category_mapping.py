import json
from path_manager import paths
from typing import Optional, Dict, List

class CategoryMapper:
    
    def __init__(self, mapping_path: str = None):
        mapping_path = mapping_path or paths.category_mapping_file
        
        with open(mapping_path, 'r') as f:
            self.mapping_config = json.load(f)
        
        self.categories = self.mapping_config['categories']
        self.keywords = self.mapping_config.get('keywords', {})
        self.project_fallback = self.mapping_config.get('project_fallback', {})
        self.default_category = self.mapping_config.get('default_category', 'Other')
        
        # Create reverse lookup for faster searching (Hash table: O(1))
        self.task_to_category = self._create_task_lookup()
    
    def _create_task_lookup(self) -> Dict[str, str]:
        """Create a reverse lookup dictionary for faster task mapping"""
        lookup = {}
        for category, tasks in self.categories.items():
            for task in tasks:
                lookup[task.lower().strip()] = category
        return lookup
    
    def map_entry_to_category(self, project: str = None, description: str = None) -> str:
        """Map a Toggl entry to a goal category based on task description"""
        
        # Clean up the description
        task_description = str(description or '').lower().strip()
        project_name = str(project or '').lower().strip()
    
        # Clean up str(NaN) → 'nan' case
        if task_description == 'nan':
            task_description = ''
        if project_name == 'nan':
            project_name = ''
        
        # Strategy 1: Exact task description match
        if task_description in self.task_to_category:
            return self.task_to_category[task_description]
        
        # Strategy 2: Keyword matching in task description
        for category, keyword_list in self.keywords.items():
            for keyword in keyword_list:
                if keyword in task_description:
                    return category
        
        # Strategy 3: Project fallback
        if project_name in self.project_fallback:
            fallback_action = self.project_fallback[project_name]
            
            if fallback_action == "check_task_description":
                # Already tried task description, return default
                return self.default_category
            else:
                return fallback_action
        
        # Strategy 4: Default category
        return self.default_category
    
    def get_category_for_row(self, row) -> str:
        """Get category for a pandas DataFrame row"""
        project = row.get('project', '')
        description = row.get('description', '')
        return self.map_entry_to_category(project, description)
    
    def add_task_to_category(self, task_description: str, category: str) -> None:
        """Add a new task to a category"""
        task_lower = task_description.lower().strip()
        
        # Add to the categories structure
        if category not in self.categories:
            self.categories[category] = []
        
        if task_lower not in [t.lower() for t in self.categories[category]]:
            self.categories[category].append(task_description)
            
        # Update the lookup dictionary
        self.task_to_category[task_lower] = category
    
    def get_tasks_for_category(self, category: str) -> List[str]:
        """Get all tasks for a specific category"""
        return self.categories.get(category, [])
    
    def get_all_categories(self) -> List[str]:
        """Get list of all categories"""
        return list(self.categories.keys())
    
    def get_unmapped_tasks(self, df) -> List[str]:
        """Get list of task descriptions that don't have category mappings"""
        unmapped = []
        for _, row in df.iterrows(): # returns index and row of dataframe
            if self.get_category_for_row(row) == self.default_category:
                task_desc = row.get('description', '').strip()
                if task_desc and task_desc not in unmapped:
                    unmapped.append(task_desc)
        return unmapped
    
    def save_mapping(self, mapping_path: str = None) -> None:
        """Save the current mapping configuration back to file"""
        mapping_path = mapping_path or paths.category_mapping_file
        
        with open(mapping_path, 'w') as f:
            json.dump(self.mapping_config, f, indent=2)
