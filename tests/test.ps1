
# python -m pip install hatch
mv __init__.py __init__.py.bak
hatch env run -e test pytest
mv __init__.py.bak __init__.py
