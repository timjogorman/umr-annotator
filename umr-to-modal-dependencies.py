import sys
from penman.penman import *
class FullUMRObject:
    def __init__(self, input_raw_umr, list_of_amrs):        
        amr_box = {}
        umr = get_amr(input_raw_umr)
        doclinkbox = {}
        for item in umr.triples():
            if item.relation == 'doclink':
                doclinkbox[item.target.strip('"')] = item.source
        amrcodec = AMRCodec()
        mapmap = {}
        all_triples = {}
        self.predicative_cores = {}
        self.all_triples = {}
        self.ac = AMRCodec()
        self.sentence_list = {}

        for sentence_id, amr in enumerate(list_of_amrs):
            its_amr = get_amr(amr)
            allvals = {}
            actualboxes = {}
            for t in its_amr.triples():
                if t.relation  == 'instance':
                    cc = "s"+str(sentence_id)+"-"+str(t.source)
                    if cc in doclinkbox:
                        actualboxes[cc] = t.source
            e2j = amrcodec.encode2json(its_amr, top=its_amr.top)
            a2d = amr2dmr_compositional(False, e2j['variable'], e2j['type'], e2j['rels'])
            s = a2d.output()
            ingraph = [x.source for x in its_amr.triples() if x.relation =='instance']
            ingraphdict = {x.source:'s'+str(sentence_id)+"-"+x.source for x in its_amr.triples() if x.relation =='instance'}
            self.sentence_list[sentence_id] = []
            for trip in its_amr.triples():
                source, relation, target = trip.source, trip.relation, trip.target
                if source in ingraphdict:
                    source = ingraphdict[source]
                if target in ingraphdict:
                    target = ingraphdict[target]
                self.sentence_list[sentence_id].append(Triple(source, relation, target))
            for each_value in actualboxes:
                ff = actualboxes[each_value]
                ss= str(a2d.get_variable(ff))
                if "(" in ss:
                    senttop = each_value.split("-")[0]+"-"                    
                    d = decode(ss)
                    mapmap[each_value] = str(d)
                    
                    toptop = senttop+d.top
                    rrr = []
                    
                    ii = []
                    for instance in d.triples():
                        source, relation, target = instance.source, instance.relation, instance.target
                        if source in ingraph:
                            source = senttop+source
                        if target in ingraph:
                            target = senttop + target
                        ii.append(Triple(source, relation, target))
                    ttg = self.ac.triples_to_graph(ii, senttop+d.top )
                    self.all_triples[each_value] =str(ttg)
        rawumr= str(umr)
        for each_point in self.all_triples:

            rawumr = rawumr.replace('"'+each_point+'"', str(self.all_triples[each_point]))

        rawdecode = decode(rawumr)
        rrr = [x for x in rawdecode.triples()]
        toptop = rawdecode.top
        done = False
        added_triples = []
        while not done:
            isfinished =True
            for each_sentence in self.sentence_list:
                sentence_id = "s"+str(each_sentence+1)
                slist = self.sentence_list[each_sentence]
                for s in slist:
                    if s in added_triples:
                        pass
                    else:   
                        if not s in rrr:
                            if s.relation == 'instance':
                                added_triples.append(s)
                                rrr.append(s)
                                isfinished =False
                            elif s.source in [x.source for x in rrr]:
                                added_triples.append(s)
                                rrr.append(s)
                                isfinished =False

            if isfinished:
                done =True
        ttg = self.ac.triples_to_graph(rrr, toptop )
        e2j = amrcodec.encode2json(ttg, top=ttg.top)
        cdict = {x.source:x.target for x in ttg.triples() if x.relation == 'instance'}
        a2d = amr2dmr_compositional(False, e2j['variable'], e2j['type'], e2j['rels'], concept_dictionary=cdict)

        aod= a2d.output2()
        print(str(decode(aod)))
        #input("###")



            
class amr2dmr_compositional:
    def __init__(self, its_type, head, concept, arguments, concept_dictionary={}):
        self.its_type = its_type
        self.var = head
        self.concept = concept
        self.concept_dictionary = concept_dictionary
        self.abox = []
        self.is_doclink = False
        for a in arguments:
            if "doclink" in a[0]:
                self.is_doclink = True
            if a[1] =='string' and '"' in str(a[2]['type']):
                self.abox.append([a[0], amr2dmr_compositional('string', False,  a[2]['type'], [], concept_dictionary=self.concept_dictionary)])
            elif a[1] =='string':
                self.abox.append([a[0], amr2dmr_compositional('nonstring',  False,  str(a[2]['type']), [], concept_dictionary=self.concept_dictionary)])
            elif a[1] =='conceptlink' and concept:
                self.abox.append([a[0], amr2dmr_compositional('concept', a[2]['variable'],  a[2]['type'], a[2]['rels'], concept_dictionary=self.concept_dictionary)])
            elif a[1] =='conceptlink' and not concept:
                self.abox.append([a[0], amr2dmr_compositional('re-entrancy', a[2]['variable'], False, [], concept_dictionary=self.concept_dictionary)])
            else:
                input("BROKEN")
    def output(self):
        tail = ''
        if self.var:
            header = "("+self.var +" / "+self.concept
            tail += ")"
        elif self.its_type == 'string':
            header = str(self.concept)
        elif self.its_type == 'nonstring':
            header = str(self.concept)
        else:
            return " "+self.concept+ " "
        e = []
        for eachline in self.abox:

            e.append(" :"+eachline[0]+" "+eachline[1].output())
        return header + "\n".join(e)+" "+tail
    def get_variable(self, variable):
        if self.var and self.var == variable:
            return self.output()
        e = ''
        for argument in self.abox:            
            e += argument[1].get_variable(variable)
        return e

    def output2(self):
        tail = ''
        swap = False
        for eachline in self.abox:

            relation = eachline[0]
            if relation == 'info-source':
                swap = (eachline[1].var, eachline[1].concept)
        if self.var:
            if swap:
                if swap[0] is None and swap[1] in self.concept_dictionary:
                    swap = (swap[1], self.concept_dictionary[swap[1]])
                header = "("+swap[0] +" / "+swap[1]
                tail += ")"
            else:
                header = "("+self.var +" / "+self.concept.replace("sentence-91","sentence-author")
                tail += ")"
        elif self.its_type == 'string':
            header = str(self.concept)
        elif self.its_type == 'nonstring':
            header = str(self.concept)
        else:
            return " "+self.concept+ " "
        e = []
        for eachline in self.abox:
            if swap and eachline[0] == 'info-source':
                pass
                #e.append(" :"+relation+" "+self.concept)
            elif eachline[0].startswith("ref") or eachline[0].startswith("distrib"):
                continue
            else:
                
                relation = eachline[0]
                if relation == 'doclink':
                    continue
                else:
                    if relation.startswith('snt') or relation.startswith(':snt') or relation.startswith('turn'):
                        relation = 'assert'

                    e.append(" :"+relation+" "+eachline[1].output2())
        return header + "\n".join(e)+" "+tail


    def drs_decode_to_modal_dep_triple(self, infosource=("r99", "ROOT"), instances_seen=[]):
        some_triple= []        
        if self.concept and self.var:
            some_triple.append(Triple(infosource[0], "pos", self.var))
            some_triple.append(Triple(self.var, "instance", self.concept))
        new_info_source = infosource
        for eachline in self.abox:
            if eachline[0] == 'info-source':
                new_info_source = (eachline[1].var, eachline[1].concept)  
        if not infosource[0] in instances_seen:
            some_triple.append(Triple(infosource[0], "instance", infosource[1]))
            instances_seen.append(infosource[0])
        for eachline in self.abox:
            relation = eachline[0]
            if relation.startswith("turn") or relation.startswith("snt"):
                relation = 'assert'
            if relation in ['assert','deny','neut']:
                ttt, infotop = eachline[1].drs_decode_to_modal_dep_triple(infosource=new_info_source, instances_seen=instances_seen)
                self.ac = AMRCodec()
                ttg = self.ac.triples_to_graph(ttt, infotop[0])
                if not new_info_source[0] == infotop[0]:
                    some_triple.append(Triple(new_info_source[0], relation, infotop[0]))
                some_triple += ttt
        return some_triple, infosource
        

def get_amr(text):
    return decode("\n".join([x for x in text.split("\n") if len(x.strip()) > 0 and not x.startswith('#')]))

def add_sentences(its_amr):
    some_triple = its_amr.ancho

input_file = sys.argv[1]
f = open(input_file).read().split("\n\n")



fuo = FullUMRObject(f[0], f[1:])