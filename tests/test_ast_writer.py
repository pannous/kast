import ast
import os
from ast import *

from astor import codegen
from kast import kast
from kast import ast_export
source=os.path.realpath(__file__)
# source='/Users/me/angle/kast/tests/hi.py'
source='/Users/me/angle/kast/ast_import.py'
source='/Users/me/angle/angle/english_parser.py'
# quit()
print(source)
contents=open(source).readlines()# all()
contents="\n".join(contents)
# contents="x.y+=1"
source="(string)" # compile from inline string source:
contents="from extension_functions import *"
# contents="range(1,2)"
# contents="def a():pass\nc=1\nif c>1:a()"
# contents="def identity(x):return x\nz=identity"
# contents="def a():pass\nimport threading\nt=threading.Thread(target=a)\nt.start()"
# contents="import threading\nt=threading.Thread(target=lambda:print('HI'))\nt.start()" #Lambda Doesn't like Print statement!!
# contents="def x():pass"
# contents="c=c+1;beep()"
# contents="1"
# contents="int(2.4)"
# contents="it=int(2.4)"
# contents="i=7;it=i-1"
# contents="xs=[1,2,3];xs.reverse();print xs"
# Module([Assign([Name('__re2sult__', Store())], Call(Name('int', Load()), [Num(2.3)], [], None, None))])
# Module([Assign([Name('it', Store())], Call(Name('int', Load()), [Num(2.4)], [], None, None))])
# contents="return 1" # 'return' outside function
# contents="print(1)"
# contents="from x import *"
# contents="x.y=1"
# contents="if 3>0:1\nelse:0"
# contents="result=1 if 3>0 else 0"
# contents="x=1;x=x+1"
# contents="def identity(x):return x\nidentity(5)"
# contents="def test():print 'yay'"
# contents="def test():result=print('yay')\nresult=test()"
# contents="def test():return print('yay')\nresult=test()"
# contents="def test():print('yay')\nresult=test()"
# contents="i=7;i-1"
# Module([Expr([Assign([Name(Str('i'), Store())], Num(7))])])
# Module([Assign([Name('i', Store())], Num(7))])
# contents="x=1;x++" # INVALID!
# contents="x=6;x%=3"
# contents="def x(y):pass"
# contents="cv.CV_WINDOW_FULLSCREEN"
# contents="return cv2.namedWindow(n, cv.CV_WINDOW_FULLSCREEN)"
#PY3:
# Module([FunctionDef('x', arguments([arg('y', None)], None, [], [], None, []), [Pass()], [], None)])

# contents="for i in [1,2,3]:print(i)"
# contents="x=y[1]"
# contents="self.x(1)"
# contents="(1 or 2) and 0" # 0  BoolOp(And(), [BoolOp(Or(), [Num(1), Num(2)]), Num(0)])
# contents="1 or 2 and 0" #1   BoolOp(Or(), [Num(1), BoolOp(And(), [Num(2), Num(0)])
# contents="@classmethod\ndef c():pass"
# contents='re.match(r"a(.*)b","acb")'
# contents="x[1:3]" #Subscript(Name('x', Load()), Slice(Num(1), Num(3), None), Load())
# contents="super(1)"
# contents="'a %s'%(1)" #BinOp(Str('a %s'), Mod(), Num(1)))
# contents="'a'+ok+'b'" #BinOp(BinOp(Str('a'), Add(), Name('ok', Load())), Add(), Str('b')))
# contents="class T:pass\ndef test(self):self.x=1\nz=T();test(z);print(z.x)" #Assign([Attribute(Name('self', Load()), attr='x', Store())], Num(1))
# contents="x[1]" # Subscript(Name('x', Load()), Index(Num(1)), Load()))
# contents="x[1]=3" # Assign(targets=[Subscript(Name('x', Load()), Index(Num(1)), Store())], value=Num(3))
# <AttrAssign name='[]='>
# 	<VCall name='variables'/>
# 	<Array>
# 		<Str value='x'/> # << TARGET
# 		<Str value='/Users/me'/> << VALUE!!
# 	</Array>
# </AttrAssign>

# It seems that the best way is using tokenize.open(): http://code.activestate.com/lists/python-dev/131251/
# code=compile(contents, source, 'eval')# import ast -> SyntaxError: invalid syntax import _ast NO IMPORT with >eval<!
# code=compile(contents, source, 'exec') # code object  AH!!!
file_ast=compile(contents, source, 'exec',ast.PyCF_ONLY_AST) # AAAAHHH!!!
# file_ast=compiler.parse(contents) #  some deprecated stuff but at least it compiles successfully!
# file_ast=compiler.parseFile(source) #  some deprecated stuff but at least it compiles successfully!
# print(file_ast)
# file_ast=compile(contents, source, 'eval',ast.PyCF_ONLY_AST) # AAAAHHH!!!


x=ast.dump(file_ast, annotate_fields=True, include_attributes=True)
print(x)
x=ast.dump(file_ast, annotate_fields=False, include_attributes=False)
print(x)
#
# file_ast=ast.parse(contents ,source,'exec')
# x=ast.dump(file_ast, annotate_fields=False, include_attributes=False)
# print(x)


# j=ast2json.ast2json(file_ast)
# print(j)
# assert code==code2
# code=compile(open(source), source, 'exec')

# import compiler # OLD! Module(None, Stmt([Discard(Add((Const(1), Const(2))))]))
# file_ast=compiler.parseFile(source)
# print(file_ast)

# file_ast=ast.parse(code ,source,'eval')
# x=ast.dump(file_ast, annotate_fields=True, include_attributes=False)
# print(x)
# file_ast=ast.parse(code ,source,'eval')

# x=ast.dump(file_ast, annotate_fields=True, include_attributes=False)


my_ast=Module(body=[
    For(
        target=Name(id='i', ctx=Store(),lineno=1, col_offset=4),
        iter=Call(
            func=Name(id='range', ctx=Load(), lineno=1, col_offset=9),
            args=[Num(n=10, lineno=1, col_offset=15)],
            keywords=[], starargs=None, kwargs=None, lineno=1, col_offset=9),
            body=[
                kast.Print(
                    value="dbg",
                    dest=None,
                    values=[Name(id='i', ctx=Load(), lineno=1, col_offset=26)],
                    nl=True,
                    lineno=1,
                    col_offset=20
                )
        ],
        orelse=[],
        lineno=1,
        col_offset=0
    )
])

my_ast=file_ast
# my_ast=Module([Assign([Attribute(Name('self', Load()), 'x', Store())], Num(1))])
# my_ast=Module([Assign([Name('self.x', Store())], Num(1))]) # DANGER!! syntaktisch korrekt aber semantisch sich nicht!!
# my_ast=Module([Assign([Name('self.x', Store())], Num(1)),Print(None, [Name('self.x', Load())], True)])
# my_ast=Module(body=[Assign(targets=[Attribute(value=Name(id='self', ctx=Load(), lineno=1, col_offset=0), attr='x', ctx=Store(), lineno=1, col_offset=0)], value=Num(n=1, lineno=1, col_offset=7), lineno=1, col_offset=0)])

ast_export.XmlExportVisitor().visit(my_ast) # => XML

source=codegen.to_source(my_ast)
print(source) # => CODE

my_ast=ast.fix_missing_locations(my_ast)
code=compile(my_ast, 'file', 'exec')
# ast_reader.emit_pyc(code)
print("GO!")
exec(code)
result=eval(code)
print(result)
# print (self.x)
