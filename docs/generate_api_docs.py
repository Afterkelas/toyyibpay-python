#!/usr/bin/env python3
"""Generate API documentation files for Sphinx."""

import os
import shutil
from pathlib import Path
from typing import List, Set

import click
from jinja2 import Environment, FileSystemLoader


# Template for module RST files
MODULE_TEMPLATE = """{{ module_name }}
{{ '=' * len(module_name) }}

.. automodule:: {{ module_path }}
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

{% if submodules %}
Submodules
----------

.. toctree::
   :maxdepth: 1

{% for submodule in submodules %}
   {{ submodule }}
{% endfor %}
{% endif %}

{% if classes %}
Classes
-------

{% for class in classes %}
.. autoclass:: {{ module_path }}.{{ class }}
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__
{% endfor %}
{% endif %}

{% if functions %}
Functions
---------

{% for function in functions %}
.. autofunction:: {{ module_path }}.{{ function }}
{% endfor %}
{% endif %}

{% if exceptions %}
Exceptions
----------

{% for exception in exceptions %}
.. autoexception:: {{ module_path }}.{{ exception }}
   :members:
   :show-inheritance:
{% endfor %}
{% endif %}
"""

# Template for the main API index
API_INDEX_TEMPLATE = """API Reference
=============

This section contains the complete API reference for the ToyyibPay Python SDK.

.. toctree::
   :maxdepth: 2
   :caption: Core Modules

   client
   async_client
   models
   config
   exceptions
   enums
   utils

.. toctree::
   :maxdepth: 2
   :caption: HTTP Layer

   http_client

.. toctree::
   :maxdepth: 2
   :caption: Webhooks

   webhooks/index

.. toctree::
   :maxdepth: 2
   :caption: Database

   db/index

.. toctree::
   :maxdepth: 2
   :caption: Resources

   resources/index
"""


class APIDocGenerator:
    """Generate API documentation for Sphinx."""
    
    def __init__(self, source_dir: Path, output_dir: Path):
        self.source_dir = source_dir
        self.output_dir = output_dir
        self.api_dir = output_dir / "api"
        
        # Setup Jinja2
        self.env = Environment(loader=FileSystemLoader(str(Path(__file__).parent)))
        
    def generate(self):
        """Generate all API documentation."""
        click.echo("🚀 Generating API documentation...")
        
        # Clean and create API directory
        if self.api_dir.exists():
            shutil.rmtree(self.api_dir)
        self.api_dir.mkdir(parents=True)
        
        # Generate module documentation
        self._generate_module_docs()
        
        # Generate index files
        self._generate_index_files()
        
        # Copy additional files
        self._copy_additional_files()
        
        click.echo("✅ API documentation generated successfully!")
    
    def _generate_module_docs(self):
        """Generate documentation for each module."""
        modules = [
            ("client", "toyyibpay.client"),
            ("async_client", "toyyibpay.async_client"),
            ("models", "toyyibpay.models"),
            ("config", "toyyibpay.config"),
            ("exceptions", "toyyibpay.exceptions"),
            ("enums", "toyyibpay.enums"),
            ("utils", "toyyibpay.utils"),
            ("http_client", "toyyibpay.http_client"),
        ]
        
        for filename, module_path in modules:
            self._write_module_doc(filename, module_path)
        
        # Generate webhook docs
        webhook_dir = self.api_dir / "webhooks"
        webhook_dir.mkdir(exist_ok=True)
        
        webhook_modules = [
            ("handler", "toyyibpay.webhooks.handler"),
            ("flask", "toyyibpay.webhooks.flask"),
            ("fastapi", "toyyibpay.webhooks.fastapi"),
        ]
        
        for filename, module_path in webhook_modules:
            self._write_module_doc(f"webhooks/{filename}", module_path)
        
        # Generate database docs
        db_dir = self.api_dir / "db"
        db_dir.mkdir(exist_ok=True)
        
        db_modules = [
            ("base", "toyyibpay.db.base"),
            ("postgres", "toyyibpay.db.postgres"),
            ("models", "toyyibpay.db.models"),
        ]
        
        for filename, module_path in db_modules:
            self._write_module_doc(f"db/{filename}", module_path)
    
    def _write_module_doc(self, filename: str, module_path: str):
        """Write documentation for a single module."""
        output_path = self.api_dir / f"{filename}.rst"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create module documentation
        content = MODULE_TEMPLATE.replace("{{ module_name }}", module_path)
        content = content.replace("{{ module_path }}", module_path)
        content = content.replace("{{ '=' * len(module_name) }}", "=" * len(module_path))
        
        # Remove template variables for unused sections
        content = content.replace("{% if submodules %}", "")
        content = content.replace("{% endif %}", "")
        content = content.replace("{% for submodule in submodules %}", "")
        content = content.replace("{% endfor %}", "")
        content = content.replace("{{ submodule }}", "")
        
        output_path.write_text(content)
        click.echo(f"  📄 Generated: {output_path.relative_to(self.output_dir)}")
    
    def _generate_index_files(self):
        """Generate index files for subdirectories."""
        # Main API index
        (self.api_dir / "index.rst").write_text(API_INDEX_TEMPLATE)
        
        # Webhooks index
        webhooks_index = """Webhook Handlers
================

.. toctree::
   :maxdepth: 1

   handler
   flask
   fastapi
"""
        (self.api_dir / "webhooks" / "index.rst").write_text(webhooks_index)
        
        # Database index
        db_index = """Database Integration
====================

.. toctree::
   :maxdepth: 1

   base
   postgres
   models
"""
        (self.api_dir / "db" / "index.rst").write_text(db_index)
        
        # Resources index
        resources_dir = self.api_dir / "resources"
        resources_dir.mkdir(exist_ok=True)
        resources_index = """API Resources
=============

.. toctree::
   :maxdepth: 1

   bills
   categories
   transactions
"""
        (resources_dir / "index.rst").write_text(resources_index)
    
    def _copy_additional_files(self):
        """Copy additional documentation files."""
        # Copy README as getting started
        readme_src = self.source_dir.parent / "README.md"
        if readme_src.exists():
            getting_started = self.output_dir / "getting_started.md"
            shutil.copy2(readme_src, getting_started)
            click.echo(f"  📄 Copied README.md to getting_started.md")
        
        # Copy ARCHITECTURE.md
        arch_src = self.source_dir.parent / "ARCHITECTURE.md"
        if arch_src.exists():
            arch_dst = self.output_dir / "architecture.md"
            shutil.copy2(arch_src, arch_dst)
            click.echo(f"  📄 Copied ARCHITECTURE.md")
        
        # Copy CHANGELOG.md
        changelog_src = self.source_dir.parent / "CHANGELOG.md"
        if changelog_src.exists():
            changelog_dst = self.output_dir / "changelog.md"
            shutil.copy2(changelog_src, changelog_dst)
            click.echo(f"  📄 Copied CHANGELOG.md")


@click.command()
@click.option(
    '--source-dir',
    default='../toyyibpay',
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help='Source code directory'
)
@click.option(
    '--output-dir',
    default='.',
    type=click.Path(file_okay=False, dir_okay=True),
    help='Output directory for documentation'
)
def main(source_dir: str, output_dir: str):
    """Generate API documentation for ToyyibPay SDK."""
    generator = APIDocGenerator(
        Path(source_dir).resolve(),
        Path(output_dir).resolve()
    )
    generator.generate()


if __name__ == '__main__':
    main()