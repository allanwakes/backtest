import types

class Robot:
    counter = 0

    def __init__(self, name):
        self.name = name

    def sayHello(self):
        return "Hi, I am " + self.name


def Rob_init(self, name):
    self.name = name


init_def = """
def Rob_init(self, name):
    self.name = name
"""

module_code = compile(init_def, '<>', 'exec')
foo_func = types.FunctionType(module_code.co_consts[0], globals())


Robot2 = type("Robot2",
              (),
              {"counter": 0,
               "__init__": foo_func,
               "sayHello": lambda self: "Hi, I am " + self.name})
x = Robot2("Marvin")
print(x.name)
print(x.sayHello())
y = Robot("Marvin")
print(y.name)
print(y.sayHello())
print(x.__dict__)
print(y.__dict__)

class_def = """
class MyRef():
    def saybye(self, name):
        print(f'bye, {name}')
"""

scope = {}
exec(class_def, scope)
Cls = scope['MyRef']
Cls().saybye('gook')