# Release Checklist for ToyyibPay Python SDK

## Pre-Release Checklist

### 1. Code Quality
- [ ] All tests pass: `pytest`
- [ ] Coverage >= 95%: `pytest --cov=toyyibpay`
- [ ] No linting errors: `make lint`
- [ ] Type checking passes: `mypy toyyibpay`
- [ ] Security scan clean: `bandit -r toyyibpay/`

### 2. Version Update
- [ ] Update version in `toyyibpay/__version__.py`
- [ ] Update version in `pyproject.toml`
- [ ] Update `CHANGELOG.md` with release notes

### 3. Documentation
- [ ] Update README.md if needed
- [ ] API docs are current
- [ ] Examples work with new version
- [ ] Migration guide for breaking changes

### 4. Test Package Build
```bash
# Clean old builds
rm -rf dist/ build/ *.egg-info

# Build package
python -m build

# Check distributions
twine check dist/*

# Verify package contents
python scripts/check_distribution.py

# Test installation in clean environment
python -m venv test_release
source test_release/bin/activate  # or test_release\Scripts\activate on Windows
pip install dist/*.whl
python -c "import toyyibpay; print(toyyibpay.__version__)"
deactivate
rm -rf test_release
```

### 5. Test on Test PyPI
```bash
# Upload to Test PyPI
twine upload --repository testpypi dist/*

# Test installation from Test PyPI
pip install --index-url https://test.pypi.org/simple/ toyyibpay
```

## Release Process

### 1. Create Release Branch
```bash
git checkout -b release/v0.1.1
git push origin release/v0.1.1
```

### 2. Tag Release
```bash
git tag -a v0.1.1 -m "Release version 0.1.1"
git push origin v0.1.1
```

### 3. Upload to PyPI
```bash
# This should be done by CI/CD, but manual backup:
twine upload dist/*
```

### 4. Create GitHub Release
- Go to GitHub releases page
- Click "Create a new release"
- Select the tag `v0.1.1`
- Add release notes from CHANGELOG.md
- Upload wheel and source dist as assets

### 5. Post-Release
- [ ] Verify package on PyPI: https://pypi.org/project/toyyibpay/
- [ ] Test installation: `pip install toyyibpay==0.1.1`
- [ ] Update documentation site
- [ ] Announce release (if applicable)

## Rollback Process

If issues are found:

### 1. Yank from PyPI (if critical)
```bash
# This marks version as "yanked" - pip won't install it by default
# Must be done from PyPI web interface
```

### 2. Fix Issues
- Create hotfix branch: `git checkout -b hotfix/v0.1.1`
- Fix the issue
- Update version to 0.1.1
- Follow release process again

## Version Numbering

Follow [Semantic Versioning](https://semver.org/):
- **MAJOR.MINOR.PATCH** (e.g., 1.2.3)
- **MAJOR**: Breaking API changes
- **MINOR**: New features, backwards compatible
- **PATCH**: Bug fixes, backwards compatible

## Common Issues

### Package includes tests/
Check `MANIFEST.in` has `prune tests`

### Import errors after install
Ensure all package imports are relative

### Missing dependencies
Check `pyproject.toml` dependencies section

### Version mismatch
Ensure version updated in all places