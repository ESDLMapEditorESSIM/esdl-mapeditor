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

class ValueTest:
    def __init__(self, ids):
        self.ids = ids


    def setid(self, ids):
        self.ids = ids

    @property
    def idfun(self):
        return self.ids

    def id2fun(self):
        return self.ids


t = ValueTest("1234")
l = [t.idfun, 5, 4]
print(l)
t.ids = "3452"
print(l)
t.setid("3452")
l2 = [t.id2fun, 5, 4]
print(l2)
t.setid("547")
print(l2[0]())

