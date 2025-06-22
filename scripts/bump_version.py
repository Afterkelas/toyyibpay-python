#!/usr/bin/env python3
"""Script to bump version numbers in the ToyyibPay SDK."""

import argparse
import re
import sys
from pathlib import Path
from typing import Tuple, Optional


def parse_version(version: str) -> Tuple[int, int, int]:
    """Parse version string into tuple of integers."""
    match = re.match(r'^(\d+)\.(\d+)\.(\d+)$', version)
    if not match:
        raise ValueError(f"Invalid version format: {version}")
    return tuple(map(int, match.groups()))


def format_version(major: int, minor: int, patch: int) -> str:
    """Format version tuple into string."""
    return f"{major}.{minor}.{patch}"


def bump_version(current: str, bump_type: str) -> str:
    """Bump version based on bump type.
    
    Args:
        current: Current version string
        bump_type: One of 'major', 'minor', 'patch'
    
    Returns:
        New version string
    """
    major, minor, patch = parse_version(current)
    
    if bump_type == 'major':
        major += 1
        minor = 0
        patch = 0
    elif bump_type == 'minor':
        minor += 1
        patch = 0
    elif bump_type == 'patch':
        patch += 1
    else:
        raise ValueError(f"Invalid bump type: {bump_type}")
    
    return format_version(major, minor, patch)


def update_file(filepath: Path, old_version: str, new_version: str) -> bool:
    """Update version in a file.
    
    Args:
        filepath: Path to file
        old_version: Current version string
        new_version: New version string
    
    Returns:
        True if file was updated, False otherwise
    """
    if not filepath.exists():
        print(f"Warning: {filepath} not found")
        return False
    
    content = filepath.read_text()
    
    # Pattern to match version assignments
    patterns = [
        # Python files: __version__ = "X.Y.Z"
        (r'__version__\s*=\s*["\']' + re.escape(old_version) + r'["\']',
         f'__version__ = "{new_version}"'),
        
        # pyproject.toml: version = "X.Y.Z"
        (r'version\s*=\s*["\']' + re.escape(old_version) + r'["\']',
         f'version = "{new_version}"'),
        
        # README or docs: v0.1.1 or toyyibpay==0.1.1
        (r'\bv?' + re.escape(old_version) + r'\b',
         new_version),
    ]
    
    updated = False
    for pattern, replacement in patterns:
        if re.search(pattern, content):
            content = re.sub(pattern, replacement, content)
            updated = True
    
    if updated:
        filepath.write_text(content)
        print(f"Updated {filepath}")
    
    return updated


def add_changelog_entry(version: str, changes: Optional[str] = None) -> None:
    """Add entry to CHANGELOG.md if it exists."""
    changelog_path = Path("CHANGELOG.md")
    if not changelog_path.exists():
        return
    
    content = changelog_path.read_text()
    
    # Create new entry
    from datetime import datetime
    date = datetime.now().strftime("%Y-%m-%d")
    
    entry = f"\n## [{version}] - {date}\n\n"
    if changes:
        entry += f"{changes}\n\n"
    else:
        entry += "### Added\n- \n\n### Changed\n- \n\n### Fixed\n- \n\n"
    
    # Insert after header
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if line.startswith('# Changelog'):
            lines.insert(i + 2, entry)
            break
    
    changelog_path.write_text('\n'.join(lines))
    print(f"Added changelog entry for {version}")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Bump version numbers")
    parser.add_argument(
        'bump_type',
        choices=['major', 'minor', 'patch'],
        help='Type of version bump'
    )
    parser.add_argument(
        '--current',
        help='Current version (auto-detected if not provided)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be changed without modifying files'
    )
    parser.add_argument(
        '--changelog',
        help='Changelog entry text'
    )
    
    args = parser.parse_args()
    
    # Get current version
    if args.current:
        current_version = args.current
    else:
        # Read from __version__.py
        version_file = Path("toyyibpay/__version__.py")
        if not version_file.exists():
            print("Error: Could not find toyyibpay/__version__.py")
            sys.exit(1)
        
        content = version_file.read_text()
        match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)
        if not match:
            print("Error: Could not find version in __version__.py")
            sys.exit(1)
        
        current_version = match.group(1)
    
    # Calculate new version
    new_version = bump_version(current_version, args.bump_type)
    
    print(f"Bumping version from {current_version} to {new_version}")
    
    if args.dry_run:
        print("DRY RUN - No files will be modified")
        return
    
    # Files to update
    files_to_update = [
        Path("toyyibpay/__version__.py"),
        Path("pyproject.toml"),
        Path("README.md"),
        Path("docs/conf.py"),
    ]
    
    # Update files
    updated_count = 0
    for filepath in files_to_update:
        if update_file(filepath, current_version, new_version):
            updated_count += 1
    
    # Update changelog
    if Path("CHANGELOG.md").exists():
        add_changelog_entry(new_version, args.changelog)
    
    print(f"\nUpdated {updated_count} files")
    print(f"New version: {new_version}")
    
    # Git commands suggestion
    print("\nNext steps:")
    print(f"1. Review changes: git diff")
    print(f"2. Commit changes: git commit -am 'Bump version to {new_version}'")
    print(f"3. Tag release: git tag -a v{new_version} -m 'Release version {new_version}'")
    print(f"4. Push: git push && git push --tags")


if __name__ == "__main__":
    main()