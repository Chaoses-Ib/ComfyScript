# Tests
```pwsh
mv __init__.py __init__.py.bak
hatch env run -e test pytest
mv __init__.py.bak __init__.py
```

## Runtime
- [`test.ps1`](runtime/test.ps1)
