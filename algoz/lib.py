import en_core_web_sm
from collections.abc import Iterable
import shelve
import spacy
import nltk

class SVO:
    # Copyright 2017 Peter de Vocht
    # use spacy small model
    nlp = en_core_web_sm.load()

    # dependency markers for subjects
    SUBJECTS = {"nsubj", "nsubjpass", "csubj", "csubjpass", "agent", "expl"}
    # dependency markers for objects
    OBJECTS = {"dobj", "dative", "attr", "oprd"}
    # POS tags that will break adjoining items
    BREAKER_POS = {"CCONJ", "VERB"}
    # words that are negations
    NEGATIONS = {"no", "not", "n't", "never", "none"}


    # does dependency set contain any coordinating conjunctions?
    def __init__(self, w):
        self.w = w
    def contains_conj(self, depSet):
        return "and" in depSet or "or" in depSet or "nor" in depSet or \
            "but" in depSet or "yet" in depSet or "so" in depSet or "for" in depSet


    # get subs joined by conjunctions
    def _get_subs_from_conjunctions(self, subs):
        more_subs = []
        for sub in subs:
            # rights is a generator
            rights = list(sub.rights)
            rightDeps = {tok.lower_ for tok in rights}
            if self.contains_conj(rightDeps):
                more_subs.extend([tok for tok in rights if tok.dep_ in self.SUBJECTS or tok.pos_ == "NOUN"])
                if len(more_subs) > 0:
                    more_subs.extend(self._get_subs_from_conjunctions(more_subs))
        return more_subs


    # get objects joined by conjunctions
    def _get_objs_from_conjunctions(self, objs):
        more_objs = []
        for obj in objs:
            # rights is a generator
            rights = list(obj.rights)
            rightDeps = {tok.lower_ for tok in rights}
            if self.contains_conj(rightDeps):
                more_objs.extend([tok for tok in rights if tok.dep_ in self.OBJECTS or tok.pos_ == "NOUN"])
                if len(more_objs) > 0:
                    more_objs.extend(self._get_objs_from_conjunctions(more_objs))
        return more_objs


    # find sub dependencies
    def _find_subs(self, tok):
        head = tok.head
        while head.pos_ != "VERB" and head.pos_ != "NOUN" and head.head != head:
            head = head.head
        if head.pos_ == "VERB":
            subs = [tok for tok in head.lefts if tok.dep_ == "SUB"]
            if len(subs) > 0:
                verb_negated = self._is_negated(head)
                subs.extend(self._get_subs_from_conjunctions(subs))
                return subs, verb_negated
            elif head.head != head:
                return self._find_subs(head)
        elif head.pos_ == "NOUN":
            return [head], self._is_negated(tok)
        return [], False


    # is the tok set's left or right negated?
    def _is_negated(self, tok):
        parts = list(tok.lefts) + list(tok.rights)
        for dep in parts:
            if dep.lower_ in self.NEGATIONS:
                return True
        return False


    # get all the verbs on tokens with negation marker
    def _find_svs(self, tokens):
        svs = []
        verbs = [tok for tok in tokens if tok.pos_ == "VERB"]
        for v in verbs:
            subs, verbNegated = self._get_all_subs(v)
            if len(subs) > 0:
                for sub in subs:
                    svs.append((sub.orth_, "!" + v.orth_ if verbNegated else v.orth_))
        return svs


    # get grammatical objects for a given set of dependencies (including passive sentences)
    def _get_objs_from_prepositions(self, deps, is_pas):
        objs = []
        for dep in deps:
            if dep.pos_ == "ADP" and (dep.dep_ == "prep" or (is_pas and dep.dep_ == "agent")):
                objs.extend([tok for tok in dep.rights if tok.dep_  in self.OBJECTS or
                            (tok.pos_ == "PRON" and tok.lower_ == "me") or
                            (is_pas and tok.dep_ == 'pobj')])
        return objs


    # get objects from the dependencies using the attribute dependency
    def _get_objs_from_attrs(self, deps, is_pas):
        for dep in deps:
            if dep.pos_ == "NOUN" and dep.dep_ == "attr":
                verbs = [tok for tok in dep.rights if tok.pos_ == "VERB"]
                if len(verbs) > 0:
                    for v in verbs:
                        rights = list(v.rights)
                        objs = [tok for tok in rights if tok.dep_ in self.OBJECTS]
                        objs.extend(self._get_objs_from_prepositions(rights, is_pas))
                        if len(objs) > 0:
                            return v, objs
        return None, None


    # xcomp; open complement - verb has no suject
    def _get_obj_from_xcomp(self, deps, is_pas):
        for dep in deps:
            if dep.pos_ == "VERB" and dep.dep_ == "xcomp":
                v = dep
                rights = list(v.rights)
                objs = [tok for tok in rights if tok.dep_ in self.OBJECTS]
                objs.extend(self._get_objs_from_prepositions(rights, is_pas))
                if len(objs) > 0:
                    return v, objs
        return None, None


    # get all functional subjects adjacent to the verb passed in
    def _get_all_subs(self, v):
        verb_negated = self._is_negated(v)
        subs = [tok for tok in v.lefts if tok.dep_ in self.SUBJECTS and tok.pos_ != "DET"]
        if len(subs) > 0:
            subs.extend(self._get_subs_from_conjunctions(subs))
        else:
            foundSubs, verb_negated =self. _find_subs(v)
            subs.extend(foundSubs)
        return subs, verb_negated


    # find the main verb - or any aux verb if we can't find it
    def _find_verbs(self, tokens):
        verbs = [tok for tok in tokens if self._is_non_aux_verb(tok)]
        if len(verbs) == 0:
            verbs = [tok for tok in tokens if self._is_verb(tok)]
        return verbs


    # is the token a verb?  (excluding auxiliary verbs)
    def _is_non_aux_verb(self, tok):
        return tok.pos_ == "VERB" and (tok.dep_ != "aux" and tok.dep_ != "auxpass")


    # is the token a verb?  (excluding auxiliary verbs)
    def _is_verb(self, tok):
        return tok.pos_ == "VERB" or tok.pos_ == "AUX"


    # return the verb to the right of this verb in a CCONJ relationship if applicable
    # returns a tuple, first part True|False and second part the modified verb if True
    def _right_of_verb_is_conj_verb(self, v):
        # rights is a generator
        rights = list(v.rights)

        # VERB CCONJ VERB (e.g. he beat and hurt me)
        if len(rights) > 1 and rights[0].pos_ == 'CCONJ':
            for tok in rights[1:]:
                if self._is_non_aux_verb(tok):
                    return True, tok

        return False, v


    # get all objects for an active/passive sentence
    def _get_all_objs(self, v, is_pas):
        # rights is a generator
        rights = list(v.rights)

        objs = [tok for tok in rights if tok.dep_ in self.OBJECTS or (is_pas and tok.dep_ == 'pobj')]
        objs.extend(self._get_objs_from_prepositions(rights, is_pas))

        #potentialNewVerb, potentialNewObjs = _get_objs_from_attrs(rights)
        #if potentialNewVerb is not None and potentialNewObjs is not None and len(potentialNewObjs) > 0:
        #    objs.extend(potentialNewObjs)
        #    v = potentialNewVerb

        potential_new_verb, potential_new_objs = self._get_obj_from_xcomp(rights, is_pas)
        if potential_new_verb is not None and potential_new_objs is not None and len(potential_new_objs) > 0:
            objs.extend(potential_new_objs)
            v = potential_new_verb
        if len(objs) > 0:
            objs.extend(self._get_objs_from_conjunctions(objs))
        return v, objs


    # return true if the sentence is passive - at he moment a sentence is assumed passive if it has an auxpass verb
    def _is_passive(self, tokens):
        for tok in tokens:
            if tok.dep_ == "auxpass":
                return True
        return False


    # resolve a 'that' where/if appropriate
    def _get_that_resolution(self, toks):
        for tok in toks:
            if 'that' in [t.orth_ for t in tok.lefts]:
                return tok.head
        return None


    # simple stemmer using lemmas
    def _get_lemma(self, word: str):
        tokens = self.nlp(word)
        if len(tokens) == 1:
            return tokens[0].lemma_
        return word


    # print information for displaying all kinds of things of the parse tree
    def printDeps(self, toks):
        for tok in toks:
            print(tok.orth_, tok.dep_, tok.pos_, tok.head.orth_, [t.orth_ for t in tok.lefts], [t.orth_ for t in tok.rights])


    # expand an obj / subj np using its chunk
    def expand(self, item, tokens, visited):
        if item.lower_ == 'that':
            temp_item = self._get_that_resolution(tokens)
            if temp_item is not None:
                item = temp_item

        parts = []

        if hasattr(item, 'lefts'):
            for part in item.lefts:
                if part.pos_ in self.BREAKER_POS:
                    break
                if not part.lower_ in self.NEGATIONS:
                    parts.append(part)

        parts.append(item)

        if hasattr(item, 'rights'):
            for part in item.rights:
                if part.pos_ in self.BREAKER_POS:
                    break
                if not part.lower_ in self.NEGATIONS:
                    parts.append(part)

        if hasattr(parts[-1], 'rights'):
            for item2 in parts[-1].rights:
                if item2.pos_ == "DET" or item2.pos_ == "NOUN":
                    if item2.i not in visited:
                        visited.add(item2.i)
                        parts.extend(self.expand(item2, tokens, visited))
                break

        return parts


    # convert a list of tokens to a string
    def to_str(self, tokens):
        if isinstance(tokens, Iterable):
            return ' '.join([item.text for item in tokens])
        else:
            return ''

    def tpl(self):
        return self.findSVOs(self.nlp(self.w))
    # find verbs and their subjects / objects to create SVOs, detect passive/active sentences
    def findSVOs(self, tokens):
        svos = []
        is_pas = self._is_passive(tokens)
        verbs = self._find_verbs(tokens)
        visited = set()  # recursion detection
        for v in verbs:
            subs, verbNegated = self._get_all_subs(v)
            # hopefully there are subs, if not, don't examine this verb any longer
            if len(subs) > 0:
                isConjVerb, conjV = self._right_of_verb_is_conj_verb(v)
                if isConjVerb:
                    v2, objs = self._get_all_objs(conjV, is_pas)
                    for sub in subs:
                        for obj in objs:
                            objNegated = self._is_negated(obj)
                            if is_pas:  # reverse object / subject for passive
                                svos.append((self.to_str(self.expand(obj, tokens, visited)),
                                            "!" + v.lemma_ if verbNegated or objNegated else v.lemma_, self.to_str(self.expand(sub, tokens, visited))))
                                svos.append((self.to_str(self.expand(obj, tokens, visited)),
                                            "!" + v2.lemma_ if verbNegated or objNegated else v2.lemma_, self.to_str(self.expand(sub, tokens, visited))))
                            else:
                                svos.append((self.to_str(self.expand(sub, tokens, visited)),
                                            "!" + v.lower_ if verbNegated or objNegated else v.lower_, self.to_str(self.expand(obj, tokens, visited))))
                                svos.append((self.to_str(self.expand(sub, tokens, visited)),
                                            "!" + v2.lower_ if verbNegated or objNegated else v2.lower_, self.to_str(self.expand(obj, tokens, visited))))
                else:
                    v, objs = self._get_all_objs(v, is_pas)
                    for sub in subs:
                        if len(objs) > 0:
                            for obj in objs:
                                objNegated = self._is_negated(obj)
                                if is_pas:  # reverse object / subject for passive
                                    svos.append((self.to_str(self.expand(obj, tokens, visited)),
                                                "!" + v.lemma_ if verbNegated or objNegated else v.lemma_, self.to_str(self.expand(sub, tokens, visited))))
                                else:
                                    svos.append((self.to_str(self.expand(sub, tokens, visited)),
                                                "!" + v.lower_ if verbNegated or objNegated else v.lower_, self.to_str(self.expand(obj, tokens, visited))))
                        else:
                            # no obj - just return the SV parts
                            svos.append((self.to_str(self.expand(sub, tokens, visited)),
                                        "!" + v.lower_ if verbNegated else v.lower_,))
        
        j = []
        for i in svos:
            i = list(i)
            while len(i)<3:
                i.append("")
            j.append(i)
        return j
def svo(w):
    return SVO(w).tpl()
def menu(u, nome="Algoz"):
    menu_options = {1:'Save Universe', 2:'Load Universe', 3: 'Add Fact', 4: 'Awser Question', 5: 'Exit',}
    while(True):
        print("\n"+nome + ">"+"Hello! My name is "+nome+", how can I help you?")
        for key in menu_options.keys():
            print (nome + ">", key, '--', menu_options[key] )
        option = int(input('Enter your choice: '))
        
        if option == 1:
            try:
                universos = shelve.open("universos")
                universos[input("Write the name of your Universe")] = u
                print("Your Universe is saved")
            except Exception as e:
                print (e)
            input(nome+"> "+"Press any key to menu")
        elif option == 2:
            try:
                universos = shelve.open("universos")
                u = universos[input("Write the name of your Universe")]
                print("Your Universe was loaded")
            except Exception as e:
                print (e)
            input(nome+"> "+"Press any key to menu")
        if option == 3:
            while True:
                # try:
                u.addFact(input('\n'+nome+">"+'Tell me your fact\n> '))
                print(nome+'>Thanks for telling me')
                # except Exception as e:
                #     print (e)
                if input(nome+"> "+"Press key 'm' to menu, or any other to add other fact") == "m":
                    break
        elif option == 4:
            while True:
                try:
                    a = input('\n'+nome+">"+'Write the subject\n> ')
                    b = input(nome+">"+'Write your assumption\n> ')
                    print(nome+"> "+"This is completely "+str(u.ansQ(a,b)))
                except Exception as e:
                    print (e)
                if input(nome+"> "+"Press key 'm' to menu, or any other to question again") == "m":
                    break
        elif option == 5:
            print(nome+"> "+'Thanks, bye bye')
            exit()
        else:
            print('\n'+nome+"> "+'Invalid option. Please enter a number between 1 and 5.')
def clausules(sentence):
    nlp = spacy.load('en_core_web_sm')
    doc = nlp(sentence)
    for token in doc:
        ancestors = [t.text for t in token.ancestors]
        children = [t.text for t in token.children]
        print(token.text, "\t", token.i, "\t", 
            token.pos_, "\t", token.dep_, "\t", 
            ancestors, "\t", children)
    def find_root_of_sentence(doc):
        root_token = None
        for token in doc:
            if (token.dep_ == "ROOT"):
                root_token = token
        return root_token
    root_token = find_root_of_sentence(doc)
    def find_other_verbs(doc, root_token):
        other_verbs = []
        for token in doc:
            ancestors = list(token.ancestors)
            if (token.pos_ == "VERB" and len(ancestors) == 1\
                and ancestors[0] == root_token):
                other_verbs.append(token)
        return other_verbs
    other_verbs = find_other_verbs(doc, root_token)
    def get_clause_token_span_for_verb(verb, doc, all_verbs):
        first_token_index = len(doc)
        last_token_index = 0
        this_verb_children = list(verb.children)
        for child in this_verb_children:
            if (child not in all_verbs):
                if (child.i < first_token_index):
                    first_token_index = child.i
                if (child.i > last_token_index):
                    last_token_index = child.i
        return(first_token_index, last_token_index)
    token_spans = []
    all_verbs = [root_token] + other_verbs
    for other_verb in all_verbs:
        (first_token_index, last_token_index) = \
        get_clause_token_span_for_verb(other_verb, doc, all_verbs)
    token_spans.append((first_token_index, last_token_index))
    sentence_clauses = []
    for token_span in token_spans:
        start = token_span[0]
        end = token_span[1]
        if (start < end):
            clause = doc[start:end]
            sentence_clauses.append(clause)
    sentence_clauses = sorted(sentence_clauses, key=lambda tup: tup[0])
    clauses_text = [clause.text for clause in sentence_clauses]
    return clauses_text
lemma = nltk.stem.WordNetLemmatizer.lemmatize
tkn = nltk.data.load('tokenizers/punkt/english.pickle').tokenize
import stanza
def heads(text, lang):
    return(stanza.Pipeline(lang=lang, processors='tokenize,mwt,pos,lemma,depparse')(text))
    # print(*[f'word: {word.text} \thead: {sent.words[word.head-1].text if word.head > 0 else "root"}\tdeprel: {word.deprel}' for sent in stanza.Pipeline(lang=lang, processors='tokenize,mwt,pos,lemma,depparse')(text).sentences for word in sent.words], sep='\n')
heads("Vou fazer assado; é melhor que tu ja venhas vindo para cá", "pt")