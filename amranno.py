import string, sys, os
import penman.penman as penman

def firstletter(concept):
    alphanum = concept[0].lower()
    if not alphanum in string.ascii_lowercase:
        alphanum = 'x'
    return alphanum
class AnnotationAMR:
    def __init__(self, initialization, isumr=False):
        self.raw=  initialization
        self.isumr=isumr
        self.codec= penman.AMRCodec(relation_sort=penman.exact_order)
        self.amr = penman.decode(initialization)
        self.allvariables = [str(x.source) for x in self.amr.anchored_triples() if x.relation =='instance']

    def newvariable(self, concept):
        alphanum = firstletter(concept)
        for q in range(1, 99):
            var = alphanum+str(q)
            if not var in self.allvariables:
                return var
    def add_concept(self, head, relation, concept):
        current_amr_in_triples = self.amr.anchored_triples()
        current_top = self.amr.top
        
        new_variable = self.newvariable(concept)

        new_amr = current_amr_in_triples + [penman.Triple(head, relation, new_variable), penman.Triple(new_variable, "instance", concept)]
        temp_amr = self.codec.triples_to_graph(new_amr, top=current_top)
        self.amr = temp_amr
        self.allvariables = [str(x.source) for x in self.amr.anchored_triples() if x.relation =='instance']
        return new_variable
    def rename_instance(self, old_head, concept):
        current_amr_in_triples = self.amr.anchored_triples()
        current_top = self.amr.top

        new_amr = [x for x in current_amr_in_triples if not x.relation == 'instance' and x.source=='old_head'] + [penman.Triple(old_head, "instance", concept)]

        temp_amr = self.codec.triples_to_graph(new_amr, top=current_top)
        str(temp_amr)
        self.amr = temp_amr
        self.allvariables = [str(x.source) for x in self.amr.anchored_triples() if x.relation =='instance']

    def addsense(self, variable, senselabel):
        triplebox = self.amr.anchored_triples()
        current_top = self.amr.top
        temp_amr2 = []
        print(variable, senselabel)
        for triple in triplebox:
            if triple.source == variable and triple.relation =='instance':
                triple = penman.Triple(variable, 'instance', triple.target + "-"+senselabel)
                #triple.concept = triple.concept + "-"+senselabel
            temp_amr2.append(triple)

        temp_amr = self.codec.triples_to_graph(temp_amr2, top=current_top)
        str(temp_amr)
        self.amr = temp_amr
        self.allvariables = [str(x.source) for x in self.amr.anchored_triples() if x.relation =='instance']


    def changetop(self, newtop):
        temp_amr = self.codec.triples_to_graph(self.amr.anchored_triples(), top=newtop)
        self.amr = temp_amr
        self.allvariables = [str(x.source) for x in self.amr.anchored_triples() if x.relation =='instance']

    def get_existing_link(self, concept):
        for triple in self.amr.anchored_triples():
            if triple.relation != 'instance' and triple.target == concept:
                return (triple.source, triple.relation)
        return False
    def add_string(self, head, relation, concept):
        current_amr_in_triples = self.amr.anchored_triples()
        current_top = self.amr.top

        new_amr = current_amr_in_triples + [penman.Triple(head, relation, concept)]
        temp_amr = self.codec.triples_to_graph(new_amr, top=current_top)
        self.amr = temp_amr
        self.allvariables = [str(x.source) for x in self.amr.anchored_triples() if x.relation =='instance']

    def delete_relation(self, head, relation, concept):
        current_amr_in_triples = self.amr.anchored_triples()
        current_top = self.amr.top
        new_amr = [x for x in current_amr_in_triples if not (x.source==head and x.relation==relation.replace(":","") and x.target==concept)]
        self.amr = self.codec.triples_to_graph(new_amr, top=current_top)
        self.allvariables = [str(x.source) for x in self.amr.anchored_triples() if x.relation =='instance']

    def delete_variable(self, variable):
        current_amr_in_triples = self.amr.anchored_triples()
        current_top = self.amr.top
        new_amr = [x for x in current_amr_in_triples if not (x.source==variable or x.target==variable)]
        self.amr = self.codec.triples_to_graph(new_amr, top=current_top)
        self.allvariables = [str(x.source) for x in self.amr.anchored_triples() if x.relation =='instance']


    def add_reentrancy(self, head, relation, concept):
        current_amr_in_triples = self.amr.anchored_triples()
        current_top = self.amr.top
        
        new_amr = current_amr_in_triples + [penman.Triple(head, relation, concept)]
        temp_amr = self.codec.triples_to_graph(new_amr, top=current_top)
        str(temp_amr)
        self.amr = temp_amr

        self.allvariables = [str(x.source) for x in self.amr.anchored_triples() if x.relation =='instance']

    def load_update(self, update_string):
        if len(update_string.strip().split(" ")) == 2:
            command, concept = update_string.strip().split(" ")    
            if command.lower() == 'top':
                newtopvariable = concept
                self.changetop(newtopvariable)
        elif len(update_string.strip().split(" ")) == 3:

            head, relation, concept = update_string.strip().split(" ")    
            if head == "replace":
                varname = relation
                try:
                    self.rename_instance(varname,  concept)
                except:
                    return False
                return True
            elif concept in self.allvariables:
                try:
                    self.add_reentrancy(head, relation, concept)
                except:
                    return False
                return True
            elif concept.endswith("-") and concept.strip("-") in self.allvariables:
                somerel = self.get_existing_link(concept.strip('-'))
                tempbox = str(self.amr)
                try:

                    self.add_reentrancy(head, relation, concept.strip('-'))
                    if somerel:

                        self.delete_relation(somerel[0], somerel[1], concept.strip('-'))
                except:
                    self.amr = penman.decode(tempbox)
                    return False
                return True
            
            else:
                try:
                    return self.add_concept(head, relation, concept)        
                except:
                    return False
                return True

        elif len(update_string.strip().split(" ")) == 4 and update_string.strip().split(" ")[0] in ['del']:
            command, head, relation, concept = update_string.strip().split(" ")
            if command.lower() == 'del':
                try:
                    self.delete_relation(head, relation, concept)
                except:
                    return False
                return True
        elif len(update_string.strip().split(" ")) > 3:

            head, relation, concept = update_string.strip().split(" ")[:3]
            all_names = update_string.strip().split(" ")[3:]
            newvar = self.add_concept(head, relation, concept)
            namevar = self.add_concept(newvar, ":name", "name")
            for opid, op in enumerate(all_names):
                self.add_string(namevar, ":op"+str(opid+1), '"'+op+'"')
            return True
        return False
