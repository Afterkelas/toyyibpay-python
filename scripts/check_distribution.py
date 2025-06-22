#!/usr/bin/env python3
"""Check what files are included in the distribution package."""

import os
import tarfile
import zipfile
from pathlib import Path


def check_distribution():
    """Check contents of distribution packages."""
    dist_dir = Path("dist")
    
    if not dist_dir.exists():
        print("No dist directory found. Run 'python -m build' first.")
        return
    
    # Check wheel contents
    for wheel_file in dist_dir.glob("*.whl"):
        print(f"\n📦 Wheel: {wheel_file.name}")
        print("=" * 50)
        
        with zipfile.ZipFile(wheel_file, 'r') as zf:
            files = sorted(zf.namelist())
            
            # Group files
            package_files = [f for f in files if f.startswith("toyyibpay/")]
            test_files = [f for f in files if "test" in f]
            metadata_files = [f for f in files if f.endswith((".dist-info/", "METADATA", "WHEEL", "RECORD"))]
            
            print(f"Package files: {len(package_files)}")
            print(f"Test files: {len(test_files)}")
            print(f"Metadata files: {len(metadata_files)}")
            
            if test_files:
                print("\n⚠️  Warning: Test files found in wheel:")
                for tf in test_files[:5]:
                    print(f"  - {tf}")
                if len(test_files) > 5:
                    print(f"  ... and {len(test_files) - 5} more")
    
    # Check source distribution contents
    for tar_file in dist_dir.glob("*.tar.gz"):
        print(f"\n📦 Source dist: {tar_file.name}")
        print("=" * 50)
        
        with tarfile.open(tar_file, 'r:gz') as tf:
            files = sorted(tf.getnames())
            
            # Group files
            package_files = [f for f in files if "/toyyibpay/" in f and ".py" in f]
            test_files = [f for f in files if "/tests/" in f]
            doc_files = [f for f in files if "/docs/" in f]
            config_files = [f for f in files if any(f.endswith(ext) for ext in [".ini", ".toml", ".yml", ".txt", ".md"])]
            
            print(f"Package files: {len(package_files)}")
            print(f"Test files: {len(test_files)}")
            print(f"Doc files: {len(doc_files)}")
            print(f"Config files: {len(config_files)}")
            
            print("\n✅ Source distribution should include tests for development")


def compare_git_vs_dist():
    """Compare files in Git vs distribution."""
    # Get all Python files in git
    git_files = set()
    for root, dirs, files in os.walk("."):
        # Skip hidden and virtual env directories
        dirs[:] = [d for d in dirs if not d.startswith(".") and d != "venv"]
        
        for file in files:
            if file.endswith(".py"):
                git_files.add(os.path.join(root, file))
    
    print(f"\n📊 Repository Statistics:")
    print(f"Total Python files in Git: {len(git_files)}")
    print(f"Test files in Git: {len([f for f in git_files if '/tests/' in f])}")
    print(f"Package files in Git: {len([f for f in git_files if '/toyyibpay/' in f and '/tests/' not in f])}")


if __name__ == "__main__":
    check_distribution()
    compare_git_vs_dist()