# Copyright (c) 2026 iak
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

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