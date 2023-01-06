import lib
import nltk

class algoz:

    class s:

        def __init__(self, n, u):
            s=self
            s.name = n
            s.element = []
            s.upperset = []
            u.append(s)

        def ad(self, a):
            self.element.append(a)

        def ud(self, a):
            self.upperset.append(a)

        def __str__(self):
            return self.name

    def __init__(self, name="algoz"):
        self.name = name
        self.u = []
        lib.menu(self) # just the Cli menu

    def iForm(self, v):
        return nltk.stem.WordNetLemmatizer.lemmatize(v, 'v') # "infinitivo do input"

    def cO(self, n):
        for i in self.u:
            if i.name == n:
                return i
        return self.s(n, self.u)

    def aD(self, v, c, condition=0):
        if self.cO(c) not in self.cO(v).element:
            self.cO(v).ad([self.cO(c), condition])
        if self.cO(v) not in self.cO(c).upperset:
            self.cO(c).ud([self.cO(v), condition])
        return [v, c]
    
    def aC(self, t):
        if t.find("if") == -1:
            return "0"
        s = ""
        for i in lib.clausules(t):  # ["clausules", "of the", "input"]
            if t.find("if")>-1:
                s = i
                break
        a = lib.svo(s) # [["Sujeito", "Verbo", "Objeto"]]
        return "int(self.ansQ('"+a[0]+"', '"+a[1]+"') or self.ansQ('"+a[0]+"', '"+a[2]+"') or self.ansQ('"+a[0]+"', '"+a[1]+a[2]+"')  )"

    def cleanData(self, t):
        t = t.lower()
        tokenizer = nltk.data.load('tokenizers/punkt/english.pickle') # ["separate.", "text.", "into.", "sentences."]
        t = tokenizer.tokenize(t)
        return t

    def addFact(self, t):
        t = self.cleanData(t)
        for j in t:
            c = self.aC(j)
            i = lib.svo(j)[0] # [["Sujeito", "Verbo", "Objeto"]]
            for k in i[2].split():
                self.aD(i[1]+" "+i[2], k, c)
            for k in i[1].split():
                self.aD(i[1], self.iForm(str(k)), c)
            self.aD(i[0], i[1]+" "+i[2], c)
            self.aD(i[1], i[2], c)
            # print(i)
            
    def ansQ(self, a, b):
        a = a.lower()
        b = b.lower()
        # for i in self.u:
        #     print(vars(i))
        c = self.cO(a).element
        # print(c)
        while True:
            d = []
            for i in c:
                i = i[eval(i[1])]
                if str(i).find(b)>-1:
                    return True
                for j in i.element:
                    if j != "" and j!=[]:
                        d.append(j) 
            c = d
            if c == []:
                return False

algoz()