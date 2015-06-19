import ast
import astor
import astor.codegen
import sys
import ast_import
import transforms.js6_export

# kast_file='test.pyast.xml'
# kast_file='test_mini.pyast.xml'
# kast_file='test_full.pyast.xml'
# kast_file='test.xast'
# kast_file='test.kast.xml'
kast_file='kast.yml'

# module=ast_import.parse_file("../samples/"+kast_file)
# module=ast_import.parse_file("hi.py")
module=ast_import.parse_file("../transforms/js6_export.py")
# print(ast.dump(module, annotate_fields=False, include_attributes=False))

indent_with=' ' * 4
add_line_information=False
generator= transforms.js6_export.JS6Visitor(indent_with, add_line_information)
generator.visit(module)
js6= ''.join(str(s) for s in generator.result)
print(js6)
fp = open ( '/tmp/out.js',"w" )
fp.write('"use strict"; // exported via js6_export')
fp.write(js6)
# fp.writelines(...)
fp.close()

import os
os.system('node /tmp/out.js')
# from pynarcissus import jsparser
 # pyjon an experimental JavaScript's eval() in Python