import pytest

import comfy_script.astutil as astutil

@pytest.mark.parametrize('s, c', [
    ('', "''"),
    ("'", "'''\\''''"),
    ("'a", "''''a'''"),
    ("a'", "'''a\\''''"),
])
def test_to_str(s, c):
    assert astutil.to_str(s) == c