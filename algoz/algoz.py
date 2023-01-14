import lib

class algoz:
    """Universe able to read, analise and respond to questions"""

    class s:
        """Named Set able with proprieties to be included and include"""

        def __init__(self, n:str, u:list):
            s=self
            s.name = n
            s.element = []
            s.upperset = []
            u.append(s)

        def __str__(self):
            return self.name
        
        def add(self, arg:str, a:list):
            if arg == "addConjSup":
                return self.addConjSup(a)
            elif arg == "addElement":
                return self.addElement(a)

        def addElement(self, a:list):
            """Adiciona elemento"""
            self.element.append(a)

        def addConjSup(self, a:list):
            """Adiciona conjunto superior"""
            self.upperset.append(a)

    def __init__(self, name="algoz"):
        self.name = name
        self.u = []
        lib.menu(self) # just the Cli menu
    
    def __str__(self):
        return self.name

    def createSet(self, n:str):
        """Create the Set named"""
        for i in self.u:
            if i.name == n:
                return i
        return self.s(n, self.u)

    def addSet(self, E:str, S:str, condition):
        """Add an element to a set"""
        case = [[self.createSet(x[0]), self.createSet(x[1]), x[2]] for x in [[E, S, "addElement"],[E, S, "addConjSup"]]]
        for [a, b, c] in case:
            if a not in b.element:
                b.add(c, [a, condition])
    
    def analizCondic(self, t:str):
        """Analize the conditions Set relations
            and returns the condition to execute as quest\n
            EM DÚVIDA\n
            EM INGLES"""
        if t.find("if") == -1:
            return 0
        s = ""
        for i in lib.clausules(t):  # ["clausules", "of the", "input"]
            if t.find("if")>-1:
                s = i
                break
        a = lib.svo(s) # [["Sujeito", "Verbo", "Objeto"]]
        return a[0]

    def addFact(self, t:str, l="br"):
        """Add a fact"""
        # t = self.cleanData(t) # ["separate.", "text.", "into.", "sentences."]
        c = self.analizCondic(t)
        t = lib.heads(t,l)
        for j in t[0]:

            self.addSet(j["text"], t[j["head"]-1]["text"], c) # incluir folha ao nó
            self.addSet(j["text"], j["upos"]) # incluir folha à classe gramatical
            self.addSet(j["text"], j["deprel"]) # incluir folha à função sintática
            self.addSet(j["text"], j["lemma"]) # incluir folha à raiz da palavra
            if lib.label(t, j["index"]) == "NP": # subjulgar à parte nominal, a verbal
                for i in lib.transverse(t, j["index"]):
                    self.addSet(i, j["text"], c)
            if lib.label(t,j["index"]) == "VP": # subjulgar à parte verbal, as outras partes
                for i in lib.transverse(t, j["index"]):
                    if lib.label(t, i["index"]) != "NP":
                        self.addSet(i, j["text"], c)

            ### com isso apenas falta o problema do pronome e do condicional
            
    def answerQuestion(self, a:str, b:str):
        """Answer if there is b in a"""
        a = a.lower()
        b = b.lower()
        c = self.createSet(a).element
        while True:
            d = []
            for i in c:
                a = 0 if i[1] == 0 else int(self.ansQ(i[1][0], i[1][1]) or self.ansQ(i[1][0], i[1][2]) or self.ansQ(i[1][0], i[1][1]+i[1][2])) # possível alteração
                if a != 0:
                    break
                i = i[0]
                if str(i).find(b)>-1:
                    return True
                for j in i.element:
                    if j != "" and j!=[]:
                        d.append(j) 
            c = d
            if c == []:
                return False

algoz()