# https://docs.python.org/release/2.7.2/library/ast.html#abstract-grammar
# https://docs.python.org/release/3.4.2/library/ast.html#abstract-grammar
# -- ASDL's six builtin types are identifier, int, string, bytes, object, >>> singleton <<< NEW

# Deprecated since version 2.6: The compiler package has been removed in Python 3.   WAAAH!! WTF! egal -> breaks a lot!!

# http://m-labs.hk/pythonparser/ PythonParser is a Python parser written specifically for use in TOOLING.
#  It parses source code into an AST that is a superset of Python s built-in ast module,
# but returns precise location information for every token

import ast
import json
import os
try:import compiler
except:print("NO compiler pyc emitter module in python3 !")
from ast import *

# todo: consider re-implementing with the visitor pattern, see astor.codegen
import kast
global ignore_position
ignore_position=True

class Ignore:
    pass

def good_fields(node):
    all=[]
    for f in node._fields:
        if not hasattr(node,f):
            print("MISSING attribute %s in %s !!!"%(f,node))
            continue
        else:
            all.append(f)
    return all

    # if isinstance(node,Name):return []
    # if isinstance(node,Num):return []
    # good=[]
    # for f in node._fields:
    #     v=node.__getattribute__(f)
    #     if isinstance(v,str): continue
    #     # if isinstance(v,list): continue
    #     if isinstance(v,expr_context):continue
    #     if isinstance(v,operator):continue
    #     if isinstance(v,cmpop):continue
    #     # if isinstance(v,Name):continue
    #     # if isinstance(v,Num):continue
    #     good.append(f)
    # return good

yet_visited={} # maps 'are' global!!
global indent
indent=0


def args(params):
    attributes=""
    for f in dir(params):
        if str(f).startswith("_"): continue
        if str(f)=="body":
            continue
        a=params.__getattribute__(f)
        if isinstance(a,list):a="["+" ".join(map(lambda ai: map_attribute(f,ai,""),a))+"]"
        if isinstance(a,dict):a=str(a)
        a=map_attribute(f,a)
        if a is Ignore: continue
        # if not a: continue
        attributes=attributes+" %s='%s'"%(f,a)
    # yet_visited[params]=True
    return attributes


def map_attribute(f, a,ignore=Ignore):
    if callable(a):return ignore
    if isinstance(a,Pass):return ignore

    # if isinstance(a,AST):return Ignore # no: Num, Name
    if isinstance(a,Num):a=a.n
    if isinstance(a,Name):a=a.id
    if isinstance(a,expr_context):a=type(a).__name__
    if isinstance(a,operator):a=type(a).__name__
    if isinstance(a,cmpop):a=type(a).__name__
    if isinstance(a,stmt):return ignore # later through fields
    if isinstance(a,expr):return ignore
    if isinstance(a,expr_context):a=type(a).__name__
    if isinstance(a,list):return ignore
    # if isinstance(a,compiler.ast.Name):a=a.name
    # if isinstance(a,compiler.ast.Num):a=a.n
    yet_visited[a]=True
    return a


def escape(param):
    return param.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")


class XmlExportVisitor(NodeVisitor):
    # def visit_arguments(self, node):
    #     print("Y")

    def generic_visit(self, node):
        if not node:
            # print("ERROR node is None!!")
            return
        global indent
        # tag = type(node).__name__
        tag = node.__class__.__name__
        if tag=="Discard":tag="CallFunc"
        if tag=="CallFunc":tag="Call"
        if tag=="From":tag="Import"
        if (isinstance(node,kast.Print) or tag=='Print'):
            pass
        if isinstance(node,compiler.ast.Name):
            print("\t"*(indent)+"<Name>"+node.name+"</Name>")
            return
        if isinstance(node,compiler.ast.Module):
            node=node.node #WTF
        if isinstance(node,compiler.ast.Function):
            node=node
        if isinstance(node,compiler.ast.Discard):
            node=node.expr #WTF
        if isinstance(node,compiler.ast.Stmt):
            node=node.nodes #WTF
        if isinstance(node,list) or isinstance(node,tuple):
            # raise Exception( "MUST NOT BE LIST: "+str(node))
            for child in node:
                self.generic_visit(child)
            return
        if isinstance(node,str) or isinstance(node,int):
            if node=="OP_ASSIGN":return
            print("\t" * (indent+1) +"<value>"+escape(str(node)))+"</value>"
            return
        if node in yet_visited:
            return
        yet_visited[node]=True

        if isinstance(node,expr_context):return
        # if isinstance(node,operator):return
        # if isinstance(node,cmpop):return
        # help(node)
        attributes=""#+" ".join(dir(node))



        if "asList" in dir(node):
            indent+=1
            print("\t" * indent + "<%s>" % (tag))
            indent+=1
            for child in node.asList():
                self.generic_visit(child)
            indent-=1
            print("\t" * indent + "</%s>" % (tag))
            indent-=1
            return


        # else:
        goodfields=dir(node)#good_fields(node)

        for f in dir(node): # Attributes
            if str(f).startswith("_"): continue
            if str(f)=="body": continue
            if str(f)=="count": continue
            if str(f)=="index": continue
            # if str(f)=="args": continue
            if ignore_position and str(f)==("col_offset"): continue
            if ignore_position and str(f)==("lineno"): continue
            if not hasattr(node,f):
                print("WARNING: MISSING Attribute: %s in %s !!"%(f,node))
                continue
            a=getattr(node,f)
            if callable(a):a=a()
            if isinstance(a,list) or isinstance(a,tuple): continue # do below!
            # a=node.__getattribute__(f)
            if isinstance(a,arguments):
                params=args(a)
                if a is Ignore:continue
                yet_visited[a]=True
                attributes=attributes+params
                continue
            a=map_attribute(f,a)
            if a is Ignore:continue
            attributes=attributes+" %s='%s'"%(f,a)
            yet_visited[a]=True
            if f in goodfields:
                goodfields.remove(f)



        # for a in node._attributes:
        #     attribs=attribs+" %s='%s'"%(a,node.__getattribute__(a))
        # for f in node._fields:
        #     a=node.__getattribute__(f)
        #     # if not (isinstance(a,str) or isinstance(a,Num)): continue
        #     if isinstance(a,Num):a=a.n
        #     attribs=attribs+" %s='%s'"%(f,a)
        # print node.body
        # print("\t" * indent + "<%s%s" % (tag, attributes), end=' ')
        if py3: print("\t" * indent + "<%s%s" % (tag, attributes), end=' ')
        if len(goodfields)==0:# and not isinstance(node,ast.Module):
            print("/>")
            return
        else:
            print(">")

        indent=indent+1
        if tag=="Name":
            print("\t" * (indent) + node.id)
            # print("\t" * (indent) + node.name)
        for f in goodfields:
            if str(f).startswith("_"): continue
            # a=node.__getattribute__(f)
            a=getattr(node,f)
            if callable(a):a=a()
            if isinstance(a,expr_context):continue
            if not isinstance(a,list) and not isinstance(a,tuple):
                if a in yet_visited:continue
                a=[a]
            if len(a)==0:continue
            if isinstance(a[0],list):
                a=a[0] #HACK!!
            print("\t" * (indent) + "<%s>" % (str(f)))
            for x in a:
                if x in yet_visited: continue
                if not x:
                    print("WARNING: None in list!")
                    continue
                indent=indent+1
                self.generic_visit(x)
                indent=indent-1
            print("\t" * (indent) + "</%s>" % (str(f)))

        # NodeVisitor.generic_visit(self, node)#??
        indent=indent-1
        print("\t" * indent + "</%s>" % (tag))


# j=json.dumps(ast.__dict__);
# j=json.dumps(ast);
# print(j)


class RewriteName(NodeTransformer):

    def visit_Name(self, node):
        return copy_location(Subscript(
            value=Name(id='data', ctx=Load()),
            slice=Index(value=Str(s=node.id)),
            ctx=node.ctx
        ), node)


def dump_xml(my_ast):
    XmlExportVisitor().visit(my_ast)

if __name__ == '__main__':
    import tests.test_ast_writer


# export?
def emit_pyc(code,fileName='output.pyc'):
    import marshal
    import py_compile
    import time
    with open(fileName, 'wb') as fc:
        fc.write(b'\0\0\0\0')
        # py_compile.wr_long(fc, long(time.time()))
        py_compile.wr_long(fc, time.time())
        marshal.dump(code, fc)
        fc.flush()
        fc.seek(0, 0)
        fc.write(py_compile.MAGIC)
        print("WRITTEN TO "+fileName)
