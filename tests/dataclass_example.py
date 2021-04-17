#  This work is based on original code developed and copyrighted by TNO 2020.
#  Subsequent contributions are licensed to you by the developers of such code and are
#  made available to the Project under one or several contributor license agreements.
#
#  This work is licensed to you under the Apache License, Version 2.0.
#  You may obtain a copy of the license at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Contributors:
#      TNO         - Initial implementation
#  Manager:
#      TNO

from dataclasses import dataclass, field, asdict
from extensions.vue_backend.messages.DLA_table_data_message import DLA_table_data_response

@dataclass
class childclass():
    a: int

@dataclass
class test():
    a: int = field(default=3)
    b: str = field(default='b')
    c: str = 'x'
    d: dict = field(default_factory=dict)
    e: list = field(default_factory=list)
    f: childclass = field(default=None)

if __name__ == '__main__':
    r = DLA_table_data_response()
    print(r)

    t = test(0, 'a')
    print(t)
    # test default values
    t = test()
    print(t)

    # use dataclasses as subclasses, they serialize realy nice
    t = test(f=childclass(2))

    # instantiate a dataclass based on a dict
    dict_test = dict()
    dict_test['a'] = 2
    dict_test['b'] = 'x'
    dict_test['c'] = 'y'
    dict_test['d'] = {'a': 3}
    dict_test['e'] = [0, 1]
    dict_test['f'] = None
    print(dict_test)
    y = test(**dict_test)
    print(y)

    # convert it back to a dict
    dict_y = asdict(y)
    print(dict_test == dict_y)

    # work with list and dicts inside a dataclass
    y.e.append('a')
    y.d['test'] = 'works'
    y.f = childclass(3)

    dict_y = asdict(y)
    print(y)
    print(dict_y)
    print(list(dict_y.values()))



