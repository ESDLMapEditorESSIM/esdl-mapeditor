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
#
#  TNO licenses this work to you under the Apache License, Version 2.0
#  You may obtain a copy of the license at http://www.apache.org/licenses/LICENSE-2.0
#
#  Contributors:
#         TNO             - Initial implementation
#
#  :license: Apache License, Version 2.0
#

import esdl
from pyecore.resources import Resource

esdl.Point.__repr__ = lambda x: 'Point(lat={})'.format(x.lat)

r = Resource()
line = esdl.Line()
r.append(line)
point1 = esdl.Point(lat=1.0, lon=1.0)
point2 = esdl.Point(lat=2.0, lon=2.0)
line.point.extend((point1, point2))

print('original -',line.point)
print('original - uri for point[0]', line.point[0].eURIFragment())
print('original - resolved object for', line.point[0].eURIFragment(), "(should be 1.0):", r.resolve(line.point[0].eURIFragment()))
print('fragment cache:', r._resolve_mem)
print()
print('reversing list')
rev = list(reversed(line.point))
line.point.clear()
line.point.extend(rev)
print()
print('reversed -',line.point)
print('reversed - uri for point[0]', line.point[0].eURIFragment())
resolved_point = r.resolve(line.point[0].eURIFragment())
print('reversed - resolved object for', line.point[0].eURIFragment(), '(should be 2.0):', resolved_point)
print('reversed - resolved uri fragment', resolved_point.eURIFragment())
print('fragment cache:', r._resolve_mem)
