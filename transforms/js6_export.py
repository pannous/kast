import ast
import astor
import astor.codegen
from astor.codegen import enclose


def _getsymbol(mapping, map_dict=None, type=type):
    """This function returns a closure that will map a
    class type to its corresponding symbol, by looking
    up the class name of an object.

    """
    if isinstance(mapping, str):
        mapping = mapping.split()
        mapping = list(zip(mapping[0::2],
                           (x.replace('_', ' ') for x in mapping[1::2])))
        mapping = dict(((getattr(ast, x), y) for x, y in mapping))
    if map_dict is not None:
        map_dict.update(mapping)

    def getsymbol(obj, fmt='%s'):
        return fmt % mapping[type(obj)]
    return getsymbol

all_symbols = {}

get_boolop = _getsymbol("""
    And and   Or or
""", all_symbols)

binops = """
    Add +   Mult *   LShift <<   BitAnd &
    Sub -   Div  /   RShift >>   BitOr  |
            Mod  %               BitXor ^
            FloorDiv //
            Pow **
"""
# MatMult @

get_binop = _getsymbol(binops, all_symbols)

get_cmpop = _getsymbol("""
  Eq    ==   Gt >   GtE >=   In    in       Is    is
  NotEq !=   Lt <   LtE <=   NotIn not_in   IsNot is_not
""", all_symbols)

get_unaryop = _getsymbol("""
    UAdd +   USub -   Invert ~   Not not
""", all_symbols)

get_anyop = _getsymbol(all_symbols)



class JS6Visitor(astor.ExplicitNodeVisitor):
    """This visitor is able to transform a well formed syntax tree into Python
    sourcecode.

    For more details have a look at the docstring of the `node_to_source`
    function.

    """

    def __init__(self, indent_with, add_line_information=False):
        self.result = []
        self.indent_with = indent_with
        self.add_line_information = add_line_information
        self.indentation = 0
        self.new_lines = 0

    def write(self, *params):
        for item in params:
            if isinstance(item, ast.AST):
                self.visit(item)
            elif hasattr(item, '__call__'):
                item()
            elif item == '\n':
                self.newline()
            else:
                if self.new_lines:
                    if self.result:
                        self.result.append('\n' * self.new_lines)
                    self.result.append(self.indent_with * self.indentation)
                    self.new_lines = 0
                self.result.append(item)

    def conditional_write(self, *stuff):
        if stuff[-1] is not None:
            self.write(*stuff)

    def newline(self, node=None, extra=0):
        self.new_lines = max(self.new_lines, 1 + extra)
        if node is not None and self.add_line_information:
            self.write('# line: %s' % node.lineno)
            self.new_lines = 1

    @enclose('{}')
    def body(self, statements):
        self.indentation += 1
        for stmt in statements:
            self.newline()
            self.visit(stmt)
        self.indentation -= 1
        self.write("\n")

    def else_body(self, elsewhat):
        if elsewhat:
            self.write('\n', ' else ')
            self.body(elsewhat)

    def body_or_else(self, node):
        self.body(node.body)
        self.else_body(node.orelse)

    def signature(self, node):
        want_comma = []

        def write_comma():
            if want_comma:
                self.write(', ')
            else:
                want_comma.append(True)

        def loop_args(args, defaults):
            padding = [None] * (len(args) - len(defaults))
            for arg, default in zip(args, padding + defaults):
                if arg.id=="self":continue
                self.write(write_comma, arg)
                self.conditional_write('=', default)

        loop_args(node.args, node.defaults)
        self.conditional_write(write_comma, '*', node.vararg)
        self.conditional_write(write_comma, '**', node.kwarg)

        kwonlyargs = getattr(node, 'kwonlyargs', None)
        if kwonlyargs:
            if node.vararg is None:
                self.write(write_comma, '*')
            loop_args(kwonlyargs, node.kw_defaults)

    def statement(self, node, *params, **kw):
        self.newline(node)
        self.write(*params)

    def decorators(self, node, extra):
        self.newline(extra=extra)
        for decorator in node.decorator_list:
            self.statement(decorator, '// decorator @', decorator)

    def comma_list(self, items, trailing=False):
        for idx, item in enumerate(items):
            if idx:
                self.write(', ')
            self.visit(item)
        if trailing:
            self.write(',')

    # Statements
    def visit_Todo(self,node):
        print ("TODO "+str(node))


    def visit_NoneType(self,node):
        self.write('None')

    def visit_Or(self,node):
        self.write( '(')
        self.visit(node.body[0])
        self.write( ' or ')
        self.visit(node.body[1])
        self.write( ')')

    def visit_And(self,node):
        self.visit(node.body[0])
        self.write( ' and ')
        self.visit(node.body[1])

    def visit_Assign(self, node):
        self.newline(node)
        for target in node.targets:
            self.write(target, ' = ')
        self.visit(node.value)

    def visit_list(self, node):
        self.write('[')
        for x in node:
            self.write(x, ', ')
        self.write(']')

    def visit_AugAssign(self, node):
        self.statement(node, node.target, get_binop(node.op, ' %s= '),
                       node.value)

    def visit_ImportFrom(self, node):
        self.statement(node, 'require (\'')
        self.comma_list(node.names)
        self.write('\')')

    def visit_ImportFrom6(self, node):
        self.write('import ') #
        for idx, item in enumerate(node.names):
            if idx:
                self.write(', ')
            self.visit(item)
        # self.comma_list(node.names)
        if node.module:
            self.write(' from ', node.module)

    def visit_Import(self, node):
        self.statement(node, 'require (')
        for module in node.names:
            self.write("'",module,"'")
        self.write(")")

    def visit_Expr(self, node):
        self.statement(node)
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        self.decorators(node, 1)
        self.statement(node, 'function %s(' % node.name)
        self.signature(node.args)
        self.write(')')
        self.body(node.body)

    def visit_ClassDef(self, node):
        have_args = []

        def paren_or_comma():
            if have_args:
                self.write(', ')
            else:
                have_args.append(True)
                self.write('(')

        self.decorators(node, 2)
        self.statement(node, 'class %s' % node.name)
        for base in node.bases:
            self.write(paren_or_comma, base)
        # XXX: the if here is used to keep this module compatible
        #      with python 2.6.
        if hasattr(node, 'keywords'):
            for keyword in node.keywords:
                self.write(paren_or_comma, keyword.arg, '=', keyword.value)
            self.conditional_write(paren_or_comma, '*', node.starargs)
            self.conditional_write(paren_or_comma, '**', node.kwargs)
        self.write(have_args and ')' or '')
        self.body(node.body)

    def visit_If(self, node):
        self.statement(node, 'if ', node.test)
        self.body(node.body)
        while True:
            else_ = node.orelse
            if len(else_) == 1 and isinstance(else_[0], ast.If):
                node = else_[0]
                self.write('\n', 'elif ', node.test)
                self.body(node.body)
            else:
                self.else_body(else_)
                break

    def visit_For(self, node):
        self.statement(node, 'for(', node.target, ' in ', node.iter,')')
        self.body_or_else(node)

    def visit_While(self, node):
        self.statement(node, 'while(', node.test,')')
        self.body_or_else(node)

    def visit_With(self, node):
        if hasattr(node, "context_expr"):  # Python < 3.3
            self.statement(node, 'with ', node.context_expr)
            self.conditional_write(' as ', node.optional_vars)
            self.write('')
        else:                              # Python >= 3.3
            self.statement(node, 'with ')
            count = 0
            for item in node.items:
                if count > 0:
                    self.write(" , ")
                self.visit(item)
                count += 1
            self.write('')
        self.body(node.body)

    # new for Python 3.3
    def visit_withitem(self, node):
        self.write(node.context_expr)
        self.conditional_write(' as ', node.optional_vars)

    def visit_NameConstant(self, node):
        self.write(node.value)

    def visit_Pass(self, node):
        self.statement(node, ';')

    def visit_Print(self, node):
        # XXX: python 2.6 only
        self.write('console.log(')
        values = node.values
        self.comma_list(values, not node.nl)
        self.write(")")

    def visit_Delete(self, node):
        self.statement(node, 'delete ')
        self.comma_list(node.targets)

    def visit_TryExcept(self, node):
        self.statement(node, 'try{')
        self.body(node.body)
        self.write("}")
        for handler in node.handlers:
            self.visit(handler)
        self.else_body(node.orelse)

    # new for Python 3.3
    def visit_Try(self, node):
        self.statement(node, 'try')
        self.body(node.body)
        for handler in node.handlers:
            self.visit(handler)
        if node.finalbody:
            self.statement(node, 'finally')
            self.body(node.finalbody)
        self.else_body(node.orelse)

    def visit_ExceptHandler(self, node):
        self.statement(node, 'except')
        if node.type is not None:
            self.write(' ', node.type)
            self.conditional_write(' as ', node.name)
        self.write(')')
        self.body(node.body)

    def visit_TryFinally(self, node):
        self.statement(node, 'try')
        self.body(node.body)
        self.statement(node, 'finally')
        self.body(node.finalbody)

    def visit_Exec(self, node):
        dicts = node.globals, node.locals
        dicts = dicts[::-1] if dicts[0] is None else dicts
        self.statement(node, 'sys.exec ', node.body)
        self.conditional_write(' in ', dicts[0])
        self.conditional_write(', ', dicts[1])

    def visit_Assert(self, node):
        self.call(node, 'assert', node.test)
        self.conditional_write(', ', node.msg)

    def visit_Global(self, node):
        pass
        # self.statement(node, 'global ', ', '.join(node.names))

    def visit_Nonlocal(self, node):
        pass

    def visit_Return(self, node):
        self.statement(node, 'return')
        self.conditional_write(' ', node.value)

    def visit_Break(self, node):
        self.statement(node, 'break')

    def visit_Continue(self, node):
        self.statement(node, 'continue')

    def visit_Raise(self, node):
        # XXX: Python 2.6 / 3.0 compatibility
        self.statement(node, 'raise')
        if hasattr(node, 'exc') and node.exc is not None:
            self.write(' ', node.exc)
            self.conditional_write(' from ', node.cause)
        elif hasattr(node, 'type') and node.type is not None:
            self.write(' ', node.type)
            self.conditional_write(', ', node.inst)
            self.conditional_write(', ', node.tback)

    # Expressions

    def visit_Attribute(self, node):
        # if node.attr.id=='==':
        #     self.write(node.value, node.attr)
        # else:
        if isinstance(node.value,ast.Name) and node.value.id=='self':
            # self.write('this.')
            self.write(node.attr)
        else:
            self.write(node.value, '.', node.attr)


    # def visit_Num(self, node):
    #     self.write(node.n)

    def instanceof(self,node):
        self.write(node.args[0]," instanceof ",node.args[1])

    def visit_Call(self, node):
        if isinstance(node.func,ast.Name) and node.func.id=="isinstance": return self.instanceof(node)

        want_comma = []

        def write_comma():
            if want_comma:
                self.write(', ')
            else:
                want_comma.append(True)

        self.visit(node.func)
        self.write('(')
        for arg in node.args:
            if isinstance(arg,ast.Name) and arg.id=="self":continue
            self.write(write_comma, arg)
        for keyword in node.keywords:
            self.write(write_comma, keyword.arg, '=', keyword.value)
        self.conditional_write(write_comma, '*', node.starargs)
        self.conditional_write(write_comma, '**', node.kwargs)
        self.write(')')

    def visit_Name(self, node):
        self.write(node.id)

    def visit_Str(self, node):
        if not 's' in dir(node):
            self.write("''")
        else:
            self.write(repr(node.s))

    def visit_Bytes(self, node):
        self.write(repr(node.s))

    def visit_Num(self, node):
        # Hack because ** binds more closely than '-'
        s = repr(node.n)
        if s.startswith('-'):
            s = '(%s)' % s
        self.write(s)

    @enclose('()')
    def visit_Tuple(self, node):
        self.comma_list(node.elts, len(node.elts) == 1)

    @enclose('[]')
    def visit_List(self, node):
        self.comma_list(node.elts)

    @enclose('{}')
    def visit_Set(self, node):
        self.comma_list(node.elts)

    @enclose('{}')
    def visit_Dict(self, node):
        for key, value in zip(node.keys, node.values):
            self.write(key, ': ', value, ', ')
            # self.write("'"+key, '\': ', value, ', ')

    @enclose('()')
    def visit_BinOp(self, node):
        self.write(node.left, get_binop(node.op, ' %s '), node.right)

    @enclose('()')
    def visit_BoolOp(self, node):
        op = get_boolop(node.op, ' %s ')
        for idx, value in enumerate(node.values):
            self.write(idx and op or '', value)

    @enclose('()')
    def visit_Compare(self, node):
        self.visit(node.left)
        for op, right in zip(node.ops, node.comparators):
            self.write(get_cmpop(op, ' %s '), right)

    @enclose('()')
    def visit_UnaryOp(self, node):
        self.write(get_unaryop(node.op), ' ', node.operand)

    def visit_Subscript(self, node):
        self.write(node.value, '[', node.slice, ']')

    def visit_Slice(self, node):
        self.conditional_write(node.lower)
        self.write('')
        self.conditional_write(node.upper)
        if node.step is not None:
            self.write('')
            if not (isinstance(node.step, ast.Name) and
                    node.step.id == 'None'):
                self.visit(node.step)

    def visit_Index(self, node):
        self.visit(node.value)

    def visit_ExtSlice(self, node):
        self.comma_list(node.dims, len(node.dims) == 1)

    def visit_Yield(self, node):
        self.write('yield')
        self.conditional_write(' ', node.value)

    # new for Python 3.3
    def visit_YieldFrom(self, node):
        self.write('yield ')
        self.visit(node.value)

    @enclose('()')
    def visit_Lambda(self, node):
        self.write('-> ')
        self.signature(node.args)
        self.write(' ', node.body)

    def visit_Ellipsis(self, node):
        self.write('...')

    def generator_visit(left, right):
        def visit(self, node):
            self.write(left, node.elt)
            for comprehension in node.generators:
                self.visit(comprehension)
            self.write(right)
        return visit

    visit_ListComp = generator_visit('[', ']')
    visit_GeneratorExp = generator_visit('(', ')')
    visit_SetComp = generator_visit('{', '}')
    del generator_visit

    @enclose('{}')
    def visit_DictComp(self, node):
        self.write(node.key, ': ', node.value)
        for comprehension in node.generators:
            self.visit(comprehension)

    @enclose('()')
    def visit_IfExp(self, node):
        self.write(node.body, ' if ', node.test, ' else ', node.orelse)

    def visit_Starred(self, node):
        self.write('*', node.value)

    @enclose('``')
    def visit_Repr(self, node):
        # XXX: python 2.6 only
        self.visit(node.value)

    def visit_Module(self, node):
        for stmt in node.body:
            self.visit(stmt)
            self.write("\n")

    # Helper Nodes

    def visit_arg(self, node):
        self.write(node.arg)
        self.conditional_write(' ', node.annotation)

    def visit_alias(self, node):
        self.write(node.name)
        self.conditional_write(' as ', node.asname)

    def visit_comprehension(self, node):
        self.write(' for(', node.target, ' in ', node.iter,')')# ' of ' ?
        if node.ifs:
            for if_ in node.ifs:
                self.write(' if ', if_)

    def visit_arguments(self, node):
        self.signature(node)

    def call(self, node, func, params):
        self.write(func,'(',params,')')
