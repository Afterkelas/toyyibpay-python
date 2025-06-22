# ToyyibPay SDK - Packaging Guide

## Repository Structure vs Package Distribution

### What's in Git (Development)
Everything needed for development and contribution:
```
toyyibpay/           ✅ Source code
tests/               ✅ All test files
docs/                ✅ Documentation source
examples/            ✅ Example applications
.github/             ✅ CI/CD workflows
requirements-dev.txt ✅ Dev dependencies
tox.ini              ✅ Testing config
pytest.ini           ✅ Test config
Makefile             ✅ Dev automation
```

### What's in PyPI Package (Distribution)
Only what users need to run the SDK:
```
toyyibpay/           ✅ Source code only
README.md            ✅ Basic docs
LICENSE              ✅ Legal requirement
requirements.txt     ✅ Runtime dependencies
tests/               ❌ Not included (saves ~500KB)
docs/                ❌ Not included (users use readthedocs)
examples/            ❌ Not included (in repo/docs)
*.ini, Makefile      ❌ Not included (dev only)
```

## Why This Approach?

### Include Tests in Git Because:
1. **Contributors need them** - How else would they verify changes?
2. **CI/CD requires them** - GitHub Actions runs tests
3. **Documentation value** - Tests show usage patterns
4. **Quality assurance** - Users can verify package works

### Exclude Tests from PyPI Because:
1. **Smaller downloads** - ~500KB smaller package
2. **Cleaner installs** - No test dependencies needed
3. **Faster installs** - Less to download/process
4. **Standard practice** - Most packages do this

## Building Packages

### Build Both Distributions
```bash
# Clean previous builds
rm -rf dist/ build/ *.egg-info

# Build wheel (binary) and sdist (source)
python -m build

# Check package contents
python scripts/check_distribution.py
```

### Verify Package Contents
```bash
# List wheel contents
unzip -l dist/*.whl | grep -E "(tests/|toyyibpay/)"

# List source dist contents  
tar -tzf dist/*.tar.gz | grep -E "(tests/|toyyibpay/)"
```

### Expected Results
- **Wheel (.whl)**: Should NOT contain `tests/` directory
- **Source dist (.tar.gz)**: MAY contain tests (for development)

## Testing Package Installation

### Test from PyPI (Production)
```bash
# Create fresh virtual environment
python -m venv test_env
source test_env/bin/activate  # or test_env\Scripts\activate on Windows

# Install from PyPI
pip install toyyibpay

# Verify
python -c "import toyyibpay; print(toyyibpay.__version__)"

# Tests not included
ls test_env/lib/python*/site-packages/toyyibpay/
# Should NOT show tests/ directory
```

### Test from Source (Development)
```bash
# Clone repository
git clone https://github.com/mwaizwafiq/toyyibpay-python.git
cd toyyibpay-python

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest  # Works because tests/ is in Git
```

## Common Issues and Solutions

### Issue: Tests included in wheel
**Solution**: Check `MANIFEST.in` has `prune tests`

### Issue: ImportError in production
**Solution**: Don't import from tests in package code

### Issue: Missing files in package
**Solution**: Check `MANIFEST.in` includes necessary files

### Issue: Package too large
**Solution**: Exclude more development files in `MANIFEST.in`

## Best Practices

1. **Always test package before publishing**
   ```bash
   pip install dist/*.whl
   python -c "import toyyibpay"
   ```

2. **Use twine check**
   ```bash
   twine check dist/*
   ```

3. **Test in clean environment**
   ```bash
   docker run -it python:3.11 bash
   pip install dist/*.whl
   ```

4. **Version control `MANIFEST.in`**
   - It controls what's in the source distribution
   - Critical for reproducible builds

## Summary

- ✅ **DO** commit tests to Git
- ✅ **DO** exclude tests from wheel distribution  
- ✅ **DO** include tests in source distribution
- ❌ **DON'T** put tests in `.gitignore`
- ❌ **DON'T** import tests from package code