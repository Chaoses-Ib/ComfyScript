'''hatch env run -e test pytest tests/test_astutil.py'''
import pytest

import comfy_script.astutil as astutil

@pytest.mark.parametrize('s, id', [
    ('', '_'),
    (':<', '_'),
    (':|', '_'),
    (':/', '_'),
])
def test_str_to_raw_id(s, id):
    assert astutil.str_to_raw_id(s) == id

@pytest.mark.parametrize('s, c', [
    ('', "''"),
    ("'", "'''\\''''"),
    ("'a", "''''a'''"),
    ("a'", "'''a\\''''"),
])
def test_to_str(s, c):
    assert astutil.to_str(s) == c

@pytest.mark.parametrize('fullname, module', [
    ('PIL.Image.Image', 'PIL.Image'),
    ('PIL.Image.Image.TEST', 'PIL.Image'),
    ('PIL.Image', 'PIL'),
    ('THONPY.Image', None),
])
def test_resolve_fullname(fullname, module):
    assert getattr(astutil.find_spec_from_fullname(fullname), 'name', None) == module