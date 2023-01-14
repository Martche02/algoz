# import stanza
# nlp = stanza.Pipeline('pt')
# doc = nlp('eu morrer hoje, amanhã há de ser outro dia .')
# print(doc)
# from nltk import ProbabilisticTree, Tree
# # Demonstrate tree parsing.
# s = "(S (NP (DT the) (NN cat)) (VP (VBD ate) (NP (DT a) (NN cookie))))"
# t = Tree.fromstring(s)
# print("Convert bracketed string into tree:")
# print(t)
# print(t.__repr__())
from nltk.tree import ParentedTree
from nltk.draw.tree import TreeView
import stanza
nlp = stanza.Pipeline(lang='pt', processors='tokenize,pos,constituency')
doc = nlp('Vai chover amanha se eu comer macarrão hoje.').sentences[0].constituency
# doc[]
t = ParentedTree.fromstring(str(doc))
leaf_values = t.leaves()
if 'eu' in leaf_values:
    leaf_index = leaf_values.index('eu') # ja determinado
    tree_location = t.leaf_treeposition(leaf_index)
    print (tree_location)
    print (ParentedTree.label(t[tree_location[0:len(tree_location)-2]]))

    # return ParentedTree.label(t[tree_location[0:len(tree_location)-1]])
ParentedTree.pretty_print(t)
# def traverse(t[tree_location[0:len(tree_location)-2]])):
#     try:
#         t.label()
#     except AttributeError:
#         return
#     else:

#         if t.height() == 2:   #child nodes
#             print t.parent()
#             return

#         for child in t:
#             traverse(child)

# traverse(ptree)