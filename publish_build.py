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

#!/usr/bin/env python3
"""
Script to publish builds to GitHub version branches
This script automates the process of creating version branches and pushing builds to GitHub
"""

import os
import sys
import subprocess
import argparse
from datetime import datetime
from build_config import BuildConfig


def run_command(cmd, cwd=None):
    """Run a shell command and return the result"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            cwd=cwd
        )
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)


def check_git_status():
    """Check if we're in a git repository"""
    success, stdout, stderr = run_command("git status --porcelain")
    if not success:
        print("Warning: Not in a git repository or git not installed")
        return False
    return True


def create_version_branch(version):
    """Create and switch to a version branch"""
    branch_name = f"v{version}"
    print(f"Creating version branch: {branch_name}")
    
    # Create and switch to the version branch
    success, stdout, stderr = run_command(f"git checkout -b {branch_name}")
    if not success:
        # If branch already exists, switch to it
        success, stdout, stderr = run_command(f"git checkout {branch_name}")
        if not success:
            print(f"Error creating/switching to branch {branch_name}: {stderr}")
            return False
    
    print(f"✓ Switched to branch: {branch_name}")
    return True


def build_project():
    """Build the project executable"""
    print("Building project...")
    
    # Run the build script
    success, stdout, stderr = run_command("python build_exe.py")
    if not success:
        print(f"Build failed: {stderr}")
        return False
    
    print("✓ Build completed successfully")
    return True


def commit_and_push(version):
    """Commit changes and push to remote"""
    branch_name = f"v{version}"
    
    # Add all files
    run_command("git add .")
    
    # Create commit
    commit_msg = f"Build release v{version} ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})"
    success, stdout, stderr = run_command(f'git commit -m "{commit_msg}"')
    
    # Create tag
    tag_success, _, tag_stderr = run_command(f"git tag -a v{version} -m 'Release version {version}'")
    if not tag_success:
        print(f"Tag creation warning: {tag_stderr}")
    
    # Push branch and tag
    print(f"Pushing to remote branch {branch_name}...")
    push_success, push_stdout, push_stderr = run_command(f"git push origin {branch_name}")
    if not push_success:
        print(f"Push to branch failed: {push_stderr}")
        return False
    
    # Push tag
    tag_push_success, _, tag_push_stderr = run_command("git push --tags")
    if not tag_push_success:
        print(f"Tag push failed: {tag_push_stderr}")
        return False
    
    print(f"✓ Successfully published build v{version} to GitHub")
    print(f"✓ Branch: {branch_name}")
    print(f"✓ Tag: v{version}")
    
    return True


def main():
    parser = argparse.ArgumentParser(description="Publish Task Chat builds to GitHub version branches")
    parser.add_argument("version", help="Version number to publish (e.g., 1.0.0)")
    parser.add_argument("--skip-build", action="store_true", help="Skip the build step, only create branch and commit")
    
    args = parser.parse_args()
    
    print(f" Publishing build v{args.version} to GitHub ".center(60, "="))
    
    # Check if we're in a git repo
    if not check_git_status():
        print("Please initialize a git repository first or navigate to your project directory.")
        sys.exit(1)
    
    # Create version branch
    if not create_version_branch(args.version):
        sys.exit(1)
    
    # Build project if not skipped
    if not args.skip_build:
        if not build_project():
            print("Build failed. Aborting publish process.")
            sys.exit(1)
    
    # Update version in config
    config = BuildConfig()
    config.update_version(args.version)
    config.save_version_file("version.json")
    
    # Commit and push to GitHub
    if commit_and_push(args.version):
        print("\n✓ Publish completed successfully!")
        print(f"Your build is now available on branch v{args.version}")
    else:
        print("\n✗ Publish failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()