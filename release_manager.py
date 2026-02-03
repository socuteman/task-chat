"""
Release Manager for Task Chat Application
Handles version management and release preparation
"""

import os
import json
import subprocess
import argparse
from datetime import datetime
from build_config import BuildConfig


def create_release_branch(version):
    """Create a new release branch for the given version"""
    branch_name = f"release/v{version}"
    print(f"Creating release branch: {branch_name}")
    
    # Create and switch to the release branch
    try:
        subprocess.run(["git", "checkout", "-b", branch_name], check=True, capture_output=True)
        print(f"✓ Successfully created branch: {branch_name}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to create branch: {e}")
        return False


def update_version_in_files(version):
    """Update version information in relevant files"""
    # Update the build_config.py file
    config_path = "build_config.py"
    
    with open(config_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace the version in the config
    import re
    content = re.sub(r'self\.version = "([^"]*)"', f'self.version = "{version}"', content)
    
    with open(config_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✓ Updated version to {version} in build_config.py")
    
    # Create/update version.json
    config = BuildConfig()
    config.update_version(version)
    config.save_version_file("version.json")


def prepare_build():
    """Prepare the build by updating version info"""
    config = BuildConfig()
    config.save_version_file("version.json")
    print("✓ Version file updated")


def tag_release(version):
    """Create a git tag for the release"""
    tag_name = f"v{version}"
    try:
        subprocess.run(["git", "tag", "-a", tag_name, "-m", f"Release version {version}"], 
                      check=True, capture_output=True)
        print(f"✓ Created tag: {tag_name}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to create tag: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Release Manager for Medical Chat Application")
    parser.add_argument("action", choices=["prepare", "release", "version"], 
                        help="Action to perform: prepare a build, create a release, or update version")
    parser.add_argument("--version", help="Version number for the release (e.g., 1.0.0)")
    
    args = parser.parse_args()
    
    if args.action == "prepare":
        prepare_build()
        print("Build preparation completed. Ready to create executable with build_exe.py")
    
    elif args.action == "release":
        if not args.version:
            print("Error: --version is required for release action")
            return
        
        # Update version in files
        update_version_in_files(args.version)
        
        # Create release branch
        if create_release_branch(args.version):
            print(f"✓ Release v{args.version} prepared successfully!")
            print(f"Next steps:")
            print(f"  1. Review changes on the release/v{args.version} branch")
            print(f"  2. Build the executable: python build_exe.py")
            print(f"  3. Test the build")
            print(f"  4. Push the branch: git push origin release/v{args.version}")
            print(f"  5. Create a pull request or push directly to main after testing")
            print(f"  6. Tag the release: python release_manager.py release --version {args.version}")
        else:
            print("Failed to create release branch.")
    
    elif args.action == "version":
        config = BuildConfig()
        version_info = config.get_version_info()
        print(json.dumps(version_info, indent=2))


if __name__ == "__main__":
    main()