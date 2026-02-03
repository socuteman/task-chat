# Copyright iak (c) 2026 Task Chat Project
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
Build configuration for Task Chat application
Used for managing version builds and releases
"""

import os
import json
from datetime import datetime

class BuildConfig:
    def __init__(self):
        self.project_name = "TaskChat"
        self.version = "1.0.0"
        self.build_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.author = "Task Chat Development Team"
        self.description = "A Flask-based web application for communication between doctors and physicists in clinical settings."
        
    def get_version_info(self):
        """Return version information as a dictionary"""
        return {
            "project_name": self.project_name,
            "version": self.version,
            "build_date": self.build_date,
            "author": self.author,
            "description": self.description
        }
    
    def update_version(self, new_version):
        """Update the version number"""
        self.version = new_version
        self.build_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
    def save_version_file(self, output_path="version.json"):
        """Save version information to a JSON file"""
        version_info = self.get_version_info()
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(version_info, f, indent=2, ensure_ascii=False)
        print(f"Version info saved to {output_path}")

# Create default build configuration
if __name__ == "__main__":
    config = BuildConfig()
    config.save_version_file()