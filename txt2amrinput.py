import sys, nltk, logging, json

from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.stem.wordnet import WordNetLemmatizer
wnl = WordNetLemmatizer()
pbjson = json.load(open('quick-propbank.json'))
sid = 0
output_file = open(sys.argv[2],'w')
for each_sentence in sent_tokenize(open(sys.argv[1]).read()):
    r = []
    if len(each_sentence.strip()) > 0:
        tokens = word_tokenize(each_sentence)
        pos = [x for x in nltk.pos_tag(tokens)]
        simpos = [x[1].lower()[0].replace("j",'a') for x in pos]
        lemmas = []
        possible_rolesets = []
        for xid, x in enumerate(tokens):
            if pos[xid][1].startswith("NNP"):
                lemmas.append(x)
            elif simpos[xid] in ['a','v','n']:
                itslem = wnl.lemmatize(x.lower(),simpos[xid])
                alias = itslem+"."+simpos[xid].replace('a','j')
                print(alias)
                possible_rolesets.extend(pbjson['aliases'].get(alias, []))
                lemmas.append(itslem)
            else:
                lemmas.append(x.lower())
        print(tokens)
        rsdefs = {x:pbjson['rolesets'].get(x, {}).get('description','') for x in list(set(possible_rolesets))}
        points = sorted([x for x in rsdefs if len(rsdefs[x]) > 0])
        defbox = " ".join([x+": "+rsdefs[x] for x in points])
        print(lemmas)
        filename = sys.argv[1]
        if "/" in filename:
            filename = filename.split("/")[-1]
        r += ["\\ref "+filename+"."+str(sid)]
        r += ["\\tx "+" ".join(tokens)]
        r += ['\\mb '+" ".join(lemmas+[x.replace(".","-").replace("_","-") for x in points])]
        r += ['\\def '+defbox]
        output_file.write("\n".join(r)+"\n\n")
        
        sid +=1