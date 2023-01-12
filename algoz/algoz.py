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

    def infinitForm(self, v:str):
        """Retorna infinitivo do verbo"""
        return lib.lemma(v, 'v') # "infinitivo do input"

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

    def cleanData(self, t:str):
        """Clean string for analysis\n
        EM INGLES"""
        t = t.lower()
        t = lib.tkn(t) # EM INGLES ["separate.", "text.", "into.", "sentences."]
        return t

    def addFact(self, t:str):
        """Add a fact"""
        t = self.cleanData(t) # ["separate.", "text.", "into.", "sentences."]

        for j in t: # "sentence"
            # separar orações
            ### localizar verbos e conjunções;
            ### entre conjunção, há uma oração
            # para cada oração 
            #### substituir pronomes por seus respectivos nomes
            #### retornar o nome, com o pronome utilizado adicionado como upperset do nome, e vice-versa
            ### determinadar pelas classes gramaticais identificadas pelo nltk
            ### para cada relação de classe contendo fluxo de ação, retornar dupla ativo-passivo
            ### cada objeto retornado na lista dupla, deve ser da classe s, com sua classe 
            ### gramatical (função sintática) raiz da palavra, e no upperset;
            #### apenas caso a palavra e sua raiz sejam iguais, 
            #### criar instancia s nomeada igual a raiz dentro da raiz
            #### retornar elemento interno
            ### para cada par de fluxo de ação retornado,
            ### adicionar de forma correta com o addSet
            # para com as conjunções, 
            # recorrer ao sentido da conjunção pré-determinado
            ## caso subordinado, subordinar o passivo ao
            ## 

            ### analizar primeira resposta https://stackoverflow.com/questions/40851783/creating-parse-trees-in-nltk-using-tagged-sentence
            ### provavelmente ao criar a arvore se desdobra as relações de fluxo da ação
            ### com isso apenas falta o problema do pronome e do condicional

            c = self.analizCondic(j)
            i = lib.svo(j)[0] # [["Sujeito", "Verbo", "Objeto"]]
            for k in i[2].split():
                self.addSet(i[1]+" "+i[2], k, c)
            for k in i[1].split():
                self.addSet(i[1], self.infinitForm(str(k)), c)
            self.addSet(i[0], i[1]+" "+i[2], c)
            self.addSet(i[1], i[2], c)
            
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