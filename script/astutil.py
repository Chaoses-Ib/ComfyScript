import sys
if sys.version_info >= (3, 11):
    from enum import StrEnum
else:
    from enum import Enum as StrEnum

import re
import keyword

def is_xid_start(s: str) -> bool:
    return s.isidentifier()

def is_xid_continue(s: str) -> bool:
    return f'_{s}'.isidentifier()

def str_to_raw_id(s: str) -> str:
    s = s.lstrip()
    assert s != ''

    if s.isascii():
        s = re.sub(r'[^A-Za-z_0-9]', '_', s)
        s = re.sub(r'^[0-9]', r'_\g<0>', s, count=1)
    else:
        s = re.sub(r'[\S\s]', lambda m: m.group(0) if is_xid_continue(m.group(0)) else '_', s)
        if not is_xid_start(s[0]):
            s = f'_{s}'
    s = re.sub(r'__+', '_', s)
    s = s.rstrip('_')
    
    if keyword.iskeyword(s):
        s += '_'
    
    return s

def id_to_lower(id: str) -> str:
    return re.sub(r'([a-z])([A-Z])', r'\1_\2', id).lower()

def id_to_camel(id: str) -> str:
    if id.isupper():
        id = id.lower()
    id = id[0].upper() + id[1:]
    id = re.sub(r'_([a-zA-Z])', lambda m: m.group(1).upper(), id)
    return id

def id_to_upper(id: str) -> str:
    return re.sub(r'([a-z])([A-Z])', r'\1_\2', id).upper()

def str_to_mod_id(s: str) -> str:
    return id_to_lower(str_to_raw_id(s))

def str_to_func_id(s: str) -> str:
    return id_to_lower(str_to_raw_id(s))

def str_to_var_id(s: str) -> str:
    id = id_to_lower(str_to_raw_id(s))
    if id == 'i':
        return 'L'
    return id

def str_to_class_id(s: str) -> str:
    return id_to_camel(str_to_raw_id(s))

def str_to_const_id(s: str) -> str:
    return id_to_upper(str_to_raw_id(s))

def to_str(s: str) -> str:
    c = ''
    if '\\' in s:
        c += 'r'
    # TODO: "" if only single ' in s
    if '\n' not in s and "'" not in s:
        c += f"'{s}'"
    else:
        # TODO: What if s contains '''?
        # TODO: Fold trailing line feeds to \n?
        c += f"'''{s}'''"
    return c

def to_assign_target_list(t: list, fold_trailing_underscores: bool = False) -> str:
    if fold_trailing_underscores:
        trailing_underscores = 0
        for i in range(len(t)):
            if t[i] == '_':
                trailing_underscores += 1
            else:
                break
        
        if trailing_underscores < 2:
            return f"{', '.join(t)}"
        else:
            return f"{', '.join(t)}, *_"
    else:
        return f"{', '.join(t)}"

# enum.py
def _is_sunder(name):
    """Returns True if a _sunder_ name, False otherwise."""
    return (len(name) > 2 and
            name[0] == name[-1] == '_' and
            name[1:2] != '_' and
            name[-2:-1] != '_')

def to_str_enum(id: str, dic: dict[str, str], indent: str) -> (str, StrEnum):
    '''
    Requires: `from enum import Enum`
    '''
    # TODO: Change to StrEnum if >= Python 3.11
    c = f'{indent}class {id}(Enum):'

    members = {}
    for (k, v) in dic.items():
        k = str_to_raw_id(k)

        # _names_ are reserved for future Enum use
        if _is_sunder(k):
            k += '_'

        # 'comfy', 'comfy++'
        while k in members:
            k += '_'
            if _is_sunder(k):
                k += '_'
        
        members[k] = v
        c += f'\n{indent}    {k} = {to_str(v)}'
    
    if len(members) == 0:
        c += f'\n{indent}    pass'
    c += '\n'
    
    return c, StrEnum(id, members)

__all__ = [
    # 'is_xid_start',
    # 'is_xid_continue',
    # 'str_to_raw_id',
    # 'id_to_lower',
    # 'id_to_camel',
    # 'id_to_upper',
    'str_to_mod_id',
    'str_to_func_id',
    'str_to_var_id',
    'str_to_class_id',
    'str_to_const_id',
    'to_str',
    'to_assign_target_list',
    'to_str_enum',
]