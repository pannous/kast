import ast

__author__ = 'me'
import ast_import


class JS6Visitor(ast.NodeVisitor):
    # def visit_arguments(self, node):
    #     print("Y")

    # def visit_Module(self,node):
    #     pass
        
    def generic_visit(self, node):
     print type(node).__name__
     ast.NodeVisitor.generic_visit(self, node)

    # def generic_visit(self, node):
    #     if not node:
    #         print("ERROR node is None!!")
    #         return
    #     print("%s"%node)


# kast_file='test.pyast.xml'
# kast_file='test_mini.pyast.xml'
# kast_file='test_full.pyast.xml'
# kast_file='test.xast'
# kast_file='test.kast.xml'
kast_file='kast.yml'

module=ast_import.parse_file("../samples/"+kast_file)

print(ast.dump(module, annotate_fields=False, include_attributes=False))

JS6Visitor().visit(module)