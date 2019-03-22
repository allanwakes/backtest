import types
class_name = 'MyOne'
init_def = """
from datetime import datetime
def one_init(self, name):
    self.name = name
    self.created_at = "init"
"""

func_def = """
def one_next(self):
    if len(self.name) > 5:
        self.created_at = "next"
    print(self.created_at)
"""

module_code = compile(init_def, '', 'exec')
# init_func = types.FunctionType(module_code.co_consts[0], globals())
init_func = types.FunctionType([c for c in module_code.co_consts if isinstance(c, types.CodeType)][0], globals())
module_code = compile(func_def, '', 'exec')
# next_func = types.FunctionType(module_code.co_consts[0], globals())
next_func = types.FunctionType([c for c in module_code.co_consts if isinstance(c, types.CodeType)][0], globals())
# i = {}
# n = {}
# exec(init_def, i)
# exec(func_def, n)

Cls = type(class_name, (), {"__init__": init_func, "next": next_func})
# Cls = type(class_name, (), {"__init__": i["one_init"], "next": n["one_next"]})
ins = Cls("allans")
ins.next()