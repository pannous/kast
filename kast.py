# https://docs.python.org/release/2.7.2/library/ast.html#abstract-grammar
# https://docs.python.org/release/3.4.2/library/ast.html#abstract-grammar

from ast import *
import ast
import sys
import _ast


py3 = sys.version < '3'


class Module(ast.Module):
	def equals(self, node, other):
		if isinstance(node, list):
			for i in len(node):
				if not self.equals(node[i], other[i]):
					return False
			return True
		if isinstance(node, ast.Str):
			node = node.s  # ignore other fields!
		if isinstance(node, str):
			if (isinstance(other, ast.Str)):
				return node == other.s
			return node == other

		for f in list(node._fields) + dir(node):
			if str(f).startswith("_"): continue
			if f == "lineno": continue
			if f == "col_offset": continue
			a = node.__getattribute__(f)
			b = other.__getattribute__(f)
			if not (type(a) == type(b) or isinstance(a, type(b))):
				return False
			if isinstance(a, list):
				for i in range(0, len(a)):
					if not self.equals(a[i], b[i]):
						return False
				continue
			if not a == b:
				return False
		return True

	def __eq__(self, other):
		for node in self.body:
			ok = False
			for cmp in other.body:
				if type(node) == type(cmp) or isinstance(node, type(cmp)):
					if self.equals(node, cmp):
						ok = True
						break
			if ok:
				continue
			return False
		return True


# class Args(list):
#     pass

def args():
	return ast.arguments(args=[Name(id='self', ctx=Load())], defaults=[], vararg=None, kwarg=None)


class Todo(ast.expr):
	pass


# (self.)call[dot[1..3]]
# Subscript(Name('x', Load()), Slice(Num(1), Num(3), None), Load())

class Return(ast.Return):
	def __init__(self, **kwargs):
		self.value = None

	def set_val(self, val):
		if isinstance(val, list): val = val[0]  # REALLY!!?
		self.value = val

	body = property(lambda self: self.value, set_val)
	variable = property(lambda self: self.value, set_val)


if sys.version_info > (3, 0):
	class TryExcept(ast.Try):
		def __init__(self, **kwargs):
			self.orelse = None
			self.handlers = []

		def set_rescue(self, r):
			self.handlers.append(r)

		rescue = property(lambda self: self.handlers, set_rescue)
else:
	class TryExcept(ast.TryExcept):
		def __init__(self, **kwargs):
			self.orelse = None
			self.handlers = []

		def set_rescue(self, r):
			self.handlers.append(r)

		rescue = property(lambda self: self.handlers, set_rescue)


class ExceptHandler(ast.ExceptHandler):
	def __init__(self, **kwargs):
		self.type = None


# name


class Eq(ast.Eq):
	def __str__(self):
		return "="


class arguments(ast.arguments):
	def __init__(self, **kwargs):
		self.args = []  # [Name(id='self',ctx=Load())]
		self.defaults = []
		self.kwarg = self.vararg = None
		super(ast.arguments, self).__init__(*kwargs)

	def set_args(self, oas):
		if not isinstance(oas, list): oas = [oas]
		if not oas[0]: return
		self.args = self.args + oas

	body = property(lambda self: self.args, set_args)


class List(ast.List):
	def __eq__(self, other):
		if isinstance(other, SyntaxError): return False
		if isinstance(other, list):
			return self.elts == other
		if isinstance(other, ast.List):
			return self.elts == other.elts
		return False


class Num(ast.Num):
	def set_value(self, n):
		self.n = n

	value = property(lambda self: self.n, set_value)

	def __repr__(self):
		return str(self.n)

	def __add__(self, other):
		self.n += other
		return self.n

	def __mul__(self, other):
		self.n *= other
		return self.n

	def __sub__(self, other):
		self.n -= other
		return self.n

	def __div__(self, other):
		self.n /= other
		return self.n

	def __eq__(self, other):
		if (isinstance(other, int)): return self.n == other
		if (isinstance(other, Num)): return self.n == other.n
		return False


class Name(ast.Name):
	def set_name(self, id):
		if (isinstance(id, ast.Name)):
			id = id.id  # WWWTTTFFF
		self.id = str(id)

	name = property(lambda self: self.id, set_name)

	def __eq__(self, other):
		return self.id == other or isinstance(other,Name) and self.id == other.id

	def __repr__(self):
		return str(self.id)  # for more beautiful debugging


def autopos(clazz):
	try:
		import the
		oldinit = clazz.__init__

		def newinit(self, *args, **kwargs):
			oldinit(self, *args, **kwargs)
			self.col_offset = the.current_offset
			self.lineno = the.line_number

		clazz.__init__ = newinit
	except:
		pass
	return clazz


@autopos
class Str(ast.Str):
	def set_value(self, s):
		if isinstance(s, ast.Name):
			s = s.id
		self.s = s

	value = property(lambda self: self.s, set_value)
	name = property(lambda self: self.s, set_value)

	def __str__(self): return self.s


class For(ast.For):
	def __init__(self, **kwargs):
		self.orelse = None

	def set_assign(self, target):
		self.target = target

	assign = property(lambda s: s.target, set_assign)

	def set_iter(self, iter):
		self.iter = iter

	call = property(lambda s: s.iter, set_iter)


class Assign(ast.Assign):
	def set_var(self, var):
		if not isinstance(var, list): var = [var]
		self.targets = var

	def set_val(self, val):
		if isinstance(val, list) and len(val) == 1: val = val[0]  # REALLY!!?
		self.value = val

	var = property(lambda self: self.targets, set_var)
	object = property(lambda self: self.targets, set_var)
	name = property(lambda self: self.targets, set_var)
	# variable = property(lambda self:self.targets, set_var)
	# variables = property(lambda self:self.targets, set_var)
	# body = property(lambda self:self.targets, set_var)
	body = property(lambda self: self.value, set_val)
	variable = property(lambda self: self.value, set_val)  # REALLY???
	variables = property(lambda self: self.value, set_val)


# a.split('b') =>
# Call(func=Attribute(value=Name(id='a', ctx=Load()), attr='split', ctx=Load()), args=[Str(s='b')],keywords=[], starargs=None, kwargs=None
#     Call(func=Name(id='print',ctx=Load()), args=Str('ok'),keywords=[], starargs=None, kwargs=None)
class Call(ast.Call):
	def __init__(self, *args, **kwargs):
		self.args = []
		self.keywords = []
		self.kwargs = self.starargs = None
		self.func = None  # Attribute(value=Name(id='self',ctx=Load()),attr=None,ctx=Load())
		super(ast.Call, self).__init__(*kwargs)

	def set_method(self, method):
		if isinstance(method, list):
			method = method[0]  # HOW?
		if (isinstance(self.func, Attribute)):
			self.func.attr = method
		else:
			self.func = method
			# self.func=Attribute(value=Name(id='self',ctx=Load()),attr=method,ctx=Load())

	method = property(lambda self: self.func, set_method)
	const = property(lambda self: self.func, set_method)
	name = property(lambda self: self.func, set_method)

	# self.x() Call(func=Attribute(value=Name('self', Load()), attr='x', Load()))
	def set_object(self, o):
		if (not isinstance(self.func, Attribute)):
			self.func = Attribute(attr=self.func, ctx=Load(), value=o)
		self.func.value = o

	def get_object(self):
		if (isinstance(self.func, Attribute)): return self.func.value
		return None

	object = property(get_object, set_object)
	variable = property(get_object, set_object)

	def set_args(self, oas):
		if not isinstance(oas, list): oas = [oas]
		# if isinstance(oas[0],arguments):oas=[oas[0].value] #lolwat??
		if not oas[0]: return
		self.args = self.args + oas

	body = property(lambda self: self.args, set_args)
	# method = property(lambda self:self.func, lambda self,method:[0 for self.func in [method]])


class ClassDef(ast.ClassDef):
	def __init__(self, **kwargs):
		self.nl = True
		self.decorator_list = []
		self.bases = []
		super(ast.ClassDef, self).__init__(*kwargs)


# todo : more beautiful mappings / defaults
class Import(ast.Import):
	def set_package(self, package):
		self.names = [package]

	def get_package(self):
		return self.names

	package = property(get_package, set_package)


class FunctionDef(ast.FunctionDef):
	def __init__(self, **kwargs):
		self.decorator_list = []
		self.body = [Pass()]
		self.args = args()
		super(ast.FunctionDef, self).__init__(*kwargs)


class __extends__(ast.Eq):
	def __str__(self):
		return "=="


# def

# _ast.Num.__str__=lambda self:"%d"%(self.n)
# _ast.Eq.__str__=lambda self:"==" #lambda self:self.num

#
# class Function(FunctionDef):
#     pass #  extended in nodes.py
#
# class Condition(ast.Compare):
#     pass  # extended in nodes.py



if py3 or sys.version_info > (3, 0):
	# PYTHON 3 HACK!!
	class Print(stmt):
		_fields = (
			'dest',
			'values',
			'nl',
		)


	# | Exec(expr body, expr? globals, expr? locals)
	class Exec(Call):
		_fields = (
			'body',
			'globals',
			'locals',
		)
else:
	@autopos
	class Print(ast.Print):
		# __metaclass__ = AutoSource
		pass


class arg(ast.Name):
	def __init__(self, name, *args, **kwargs):
		super(arg, self).__init__(*args, **kwargs)
		self.ctx = Param()
		self.id = name
		# super(arg, self).__init__(*args, **kwargs)
		# super(ast.Name,self).__init__(*kwargs)
		# _attributes = (
		#     'lineno',
		#     'col_offset',
		# )
		# _fields = (
		#     'arg',
		#     'annotation',
		# )

# class Name(ast.Name):
#     # def __init__(self, **kwargs):
#     #     super(ast.Name,self).__init__(*kwargs)
#     def __str__(self):
#         if not 'id' in self._attributes: self.id="MISSING_ID!!!"
#         return "<kast.Name id='%s'>"%self.id

types = {  # see _ast.py , F12:
	"Raise": Raise,  # danger raise keyword
	"class": ClassDef,
	"operator": operator,
	"Add": Add,
	"alias": alias,
	"boolop": boolop,
	"And": And,
	"arguments": arguments,
	"stmt": stmt,
	"Assert": Assert,
	"Assign": Assign,
	"expr": expr,
	"Attribute": Attribute,
	"AugAssign": AugAssign,
	"expr_context": expr_context,
	"AugLoad": AugLoad,
	"AugStore": AugStore,
	"BinOp": BinOp,
	"BitAnd": BitAnd,
	"BitOr": BitOr,
	"BitXor": BitXor,
	"BoolOp": BoolOp,
	"Break": Break,
	"Call": Call,
	"ClassDef": ClassDef,
	"cmpop": cmpop,
	"Compare": Compare,
	"comprehension": comprehension,
	"Continue": Continue,
	"Del": Del,
	"Delete": Delete,
	"Dict": Dict,
	"DictComp": DictComp,
	"Div": Div,
	"slice": slice,
	"Ellipsis": Ellipsis,
	"Eq": Eq,
	"excepthandler": excepthandler,
	"ExceptHandler": ExceptHandler,
	"Exec": Exec,
	"Expr": Expr,
	"mod": mod,
	"Expression": Expression,
	"ExtSlice": ExtSlice,
	"FloorDiv": FloorDiv,
	"For": For,
	"FunctionDef": FunctionDef,
	"GeneratorExp": GeneratorExp,
	"Global": Global,
	"Gt": Gt,
	"GtE": GtE,
	"If": If,
	"IfExp": IfExp,
	"Import": Import,
	"ImportFrom": ImportFrom,
	"In": In,
	"Index": Index,
	"Interactive": Interactive,
	"unaryop": unaryop,
	"Invert": Invert,
	"Is": Is,
	"IsNot": IsNot,
	"keyword": keyword,
	"Lambda": Lambda,
	"List": List,
	"ListComp": ListComp,
	"Load": Load,
	"LShift": LShift,
	"Lt": Lt,
	"LtE": LtE,
	"Mod": Mod,
	"Module": Module,
	"Mult": Mult,
	"Name": Name,
	"Not": Not,
	"NotEq": NotEq,
	"NotIn": NotIn,
	"Num": Num,
	"Or": Or,
	"Param": Param,
	"Pass": Pass,
	"Pow": Pow,
	"Print": Print,
	'Raise': Raise,
	"Return": Return,
	"RShift": RShift,
	"Set": Set,
	"SetComp": SetComp,
	"Slice": Slice,
	"Store": Store,
	"Str": Str,
	"Sub": Sub,
	"Subscript": Subscript,
	"Suite": Suite,
	"TryExcept": TryExcept,
	"Tuple": Tuple,
	"UAdd": UAdd,
	"UnaryOp": UnaryOp,
	"USub": USub,
	"While": While,
	"With": With
}

if sys.version_info < (3, 0):
	types["Repr"] = ast.Repr
	types["TryFinally"] = ast.TryFinally

# workaround: alias is keyword in ruby!
mapped_types = {
	"Arguments": arguments,
	# "Block":Module, #NOT REALLY!
	"Variable": Name,
	"Const": Name,  # todo
	"Class": ClassDef,
	# "Alias":alias, Assign a=b
	"Argument": Name,
	# "Default":
	"Hash": Dict,
	"String": expr,  # str or binop('a',add,'b')
	"Begin": TryExcept,
	"Defs": Todo,  # FunctionDef(name='?', args=args(),body=[],decorator_list=[Name(id='classmethod', ctx=Load())]),

	# "Arguments":arguments,
	# "Args":arguments,
	# "Args":List, # Args, AAARRG!!! ;)

	"class_method": FunctionDef,
# FunctionDef(name='x', args=arguments(args=[], vararg=None, kwarg=None, defaults=[]) WTF
	# "class_method":FunctionDef, # todo !!
	"Method": FunctionDef,
	"int": Num,
	"let": Assign,
	"Symbol": Str,  # Name, a: b => 'a':b !!
	"Literal": Name,
	"Condition": expr,
	"Dot": Todo,
	"Regexp": Str,  # ! r'.' == "." !!!
	"Rescue": ExceptHandler,
	"Self": Name(id='self', ctx=Load()),
	"Super": Call,
	"Yield": Todo,  # Yield, #NOOO ;)
	"Value": expr,
	"Then": expr  # Value
}

for k in types.keys():
	if (k == 'Raise'): continue
	if (k == 'Let'): continue
	mapped_types[k.lower()] = types[k]
	mapped_types["{http://angle-lang.org}" + k.lower()] = types[k]

types.update(mapped_types)

assert Name(id='xyz', ctx=Load()) == 'xyz'
# Equality hack

def name(param):
	if (isinstance(param, ast.Name)): return param
	if type(param).__name__ == "Variable":
		param = param.name
	return Name(id=param, ctx=Load())


def store(param):
	if (isinstance(param, ast.Name)): return param
	if type(param).__name__ == "Variable":
		param = param.name
	return Name(id=param, ctx=Store())


def call(func, args):
	if isinstance(func, str):    func = name(func)
	if not isinstance(args, list): args = [args]
	return ast.Call(func=func, args=args, keywords=[], starargs=None, kwargs=None)


def call_attribute(obj, func, *args, **vargs):
	if isinstance(func, ast.Name): func = func.id
	if not isinstance(args, list): args = [args]
	if args == [()]: args = []
	keywords = []
	for k, v in vargs.items():
		keywords.append(keyword(k, v))
	return ast.Call(func=ast.Attribute(value=name(obj), attr=func, ctx=Load()), args=args, keywords=keywords,
									starargs=None, kwargs=None)
	# Call(func=Attribute(value=Name(id='a', ctx=Load()), attr='split', ctx=Load()), args=[Str(s='b')]


def assign(k, param):
	if (isinstance(param, ast.Pass)):
		param = None  # ast.None
		return param
	targets = [name(k)]
	for t in targets:
		t.ctx = Store()
	if isinstance(param, ast.Name):
		param.ctx = Load()
	return Assign(targets, param)

def num(n):
	if isinstance(n,Num):return n
	return Num(n)


#  automatically add the current token position
def decorate(clazz):
	try:
		import the
		oldinit = clazz.__init__

		def newinit(self, *args, **kwargs):
			oldinit(self, *args, **kwargs)
			self.col_offset = the.current_offset
			self.lineno = the.line_number

		clazz.__init__ = newinit
	except:
		pass


def decorate_all():
	pass
# for type in types.values():
#     decorate(type)
decorate_all()

# Python 3.4 introduced a new node of type NameConstant for True,False & None.
none = name("None")
nil = name("None")
null = name("None")
false = name("False")
true = name("True")
Self = name('self')
zero = Num(0)
one = Num(1)
