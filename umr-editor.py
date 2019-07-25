import PySimpleGUI as sg
import penman, string, sys, os
from amranno import *


class UMRfile:
    def __init__(self, rawtext, filename):
        inumr = False
        inamr = False
        lastsent = False
        self.filename = filename
        self.rawtextarray = []
        self.amrs = []
        self.amrids = {}
        self.sentences = {}
        self.umr = []
        self.its_amr=None
        self.focus = 0
        self.stack = []
        amrbuffer = []
        for line in rawtext.split("\n"):
            if "# ::umr" in line:
                inumr = True

            elif "# ::id" in line:
                inumr = False
                if len(amrbuffer) > 0 and inamr:
                    rawamr = "\n".join(amrbuffer)
                    self.amrids[len(self.amrs)] = inamr
                    self.sentences[len(self.amrs)] = lastsent
                    self.amrs.append(rawamr)
                    amrbuffer = []
                inamr = line.split("::id")[1]
                if "::" in inamr:
                    inamr = inamr.split("::")[0].strip()
            elif "# ::snt" in line:
                lastsent = line.split("::snt")[1].strip()
            elif inumr:
                self.umr.append(line)
            elif len(line.strip()) > 0 and not line.startswith("#"):
                amrbuffer.append(line.strip("\n"))
            if not inumr:
                self.rawtextarray.append(line)
        if len(amrbuffer) > 0 and inamr:
            rawamr = "\n".join(amrbuffer)
            self.amrids[len(self.amrs)] = inamr
            self.sentences[len(self.amrs)] = lastsent
            self.amrs.append(rawamr)
    def push(self):
        self.stack.append(str(self.its_amr.amr))
        while len(self.stack) > 20:

            self.stack.pop(0)

    def undo(self):
        if len(self.stack) > 1:
            self.stack.pop()
            sq = str(self.stack.pop())
            print(sq)
        self.its_amr.amr = penman.decode(sq)
    def get_concept(self, variable):
        itsamr = self.amrs[self.focus]            
        some_amr=  penman.decode(itsamr)
        e = [x.target for x in some_amr.triples() if x.relation == 'instance' and x.source==variable]
        return e
    def currentumr(self):
        return "\n".join(self.umr)
    def prettyamr(self):
        return "\n\n".join(self.amrs)
    def save(self):
        with open(self.filename+".umr",'w') as annotatedfile:
            annotatedfile.write("# ::umr\n"+str(self.its_amr.amr)+"\n\n"+"\n".join(self.rawtextarray))
            return True
        return False
    def returnColumns(self):
        layouts = []
        for amrid, a in enumerate(self.amrs):
            if amrid == self.focus:
                layouts.append([sg.Text(self.sentences[amrid]+"\n"+str(a),key="SUB"+str(amrid), font=("Times",12,""),text_color="#000000")])
            else:
                layouts.append([sg.Text(self.sentences[amrid]+"\n"+str(a),key="SUB"+str(amrid), font=("Times",12,""),text_color="#a5bbb2")])

        amr_box = sg.Column(layouts,
        size=(850, 660),
        scrollable=True,
        key="_RAWAMR_",
        visible=True)
        return amr_box, layouts
def annotateUMR(rawfile, filename):
    sg.SetOptions(background_color='#FFFFFF', element_background_color='#FFFFFF', text_element_background_color='#FFFFFF',input_elements_background_color='#FFFFFF')

    umrf = UMRfile(rawfile, filename)
    amr_box, layouts = umrf.returnColumns()
    sgt = [[sg.Text('', size=(750,800), key='_OUTPUT_')]]
    display_box = sg.Column(sgt,
        size=(550, 700),
        scrollable=True)
    layout = [[amr_box, display_box],
              [sg.Input(key='_IN_')],
              [sg.Text('', size=(10,1), key='_STATUS_')],
              [sg.Button('Show', bind_return_key=True), sg.Button('Exit')]]

    window = sg.Window('Make an AMR', layout, background_color='#FFFFFF', size=(1250,850), resizable=True).Finalize()
    umrf.its_amr = AnnotationAMR(umrf.currentumr(), isumr=True)
    window.Element('_OUTPUT_').Update(str(umrf.its_amr.amr))
    while True:  # Event Loop
        amr_box, layouts = umrf.returnColumns()
        for lid, l in enumerate(layouts):
            if lid == umrf.focus:
                window.Element('SUB'+str(lid)).Update(font=("Times",12,""), text_color="#000000")
            else:
                window.Element('SUB'+str(lid)).Update(font=("Times",12,""),text_color="#a5bbb2")
        event, values = window.Read()
        print(event, values)
        if event is None or event == 'Exit':
            break
        status = ''
        umrf.push() 
        didsave = umrf.save()
        if "focus=" in values['_IN_']:
            val = values['_IN_'].split("focus=")[1].strip()
            umrf.focus = int(val)
        elif "undo" == values['_IN_'].strip():
            umrf.undo()
        elif "save" == values['_IN_'].strip():
            didsave = umrf.save()
            if didsave:
                status ="successfully saved"
            else:
                status ="failed to save"
        elif values['_IN_'].endswith("!") and len(values['_IN_'].strip().split(" ")) ==3:
            target = values['_IN_'].strip().strip("!").split(" ")[-1]
            head, relation, __ = values['_IN_'].strip().split(" ")
            concept = umrf.get_concept(target)
            if len(concept) > 0:
                newf = umrf.its_amr.add_concept(head, relation, concept[0])
                umrf.its_amr.add_string(newf, "doclink", '"s'+str(umrf.focus)+"-"+target+'"')    
            else:
                status = "No variable "+target+ " in that AMR"
        elif values['_IN_'].startswith("renamerel") and len(values['_IN_'].strip().split(" ")) == 5:
            __, head, relation, target, newrelation = values['_IN_'].strip().split(" ")
            umrf.its_amr.add_reentrancy(head, newrelation, target)    
            umrf.its_amr.delete_relation(head, relation, target)
        elif values['_IN_'].startswith("del") and len(values['_IN_'].strip().split(" ")) ==2:
            umrf.its_amr.delete_variable(values['_IN_'].strip().split(" ")[1])
        else:
            q = umrf.its_amr.load_update(values['_IN_'])
            if not q:
                status = "could not parse "+values['_IN_']
        if event == 'Show':
            if umrf.its_amr is not None:
                values['_IN_'] = ''
                window.Element('_IN_').Update('')
                window.Element('_STATUS_').Update(status)
                window.Element('_OUTPUT_').Update(str(umrf.its_amr.amr))
    window.Close()
if __name__ == "__main__":
    fn = sys.argv[1]
    try:
        style = sys.argv[2]
        assert style in ['unm','cu']
    except:
        style = 'cu'


    if os.path.exists(fn+".umr"):
        rawtext = open(fn+".umr").read()
    else:
        rawtext = open(fn).read()
        if not "::umr" in rawtext:
            if style == 'cu':
                rawtext += "# ::umr \n(u1 / utterance :info-source (a / author)"
                for q in range(rawtext.count("::id")):
                    rawtext += "   :snt"+str(q)+"(s"+str(q+1)+" / sentence-91)\n"
                rawtext += ")\n\n"
            elif style == 'unm':
                rawtext += "# ::umr \n(d / document "
                for q in range(rawtext.count("::id")):
                    rawtext += "   :snt"+str(q)+"(s"+str(q+1)+" / root :modal-source (a"+str(q+1)+" / auth))\n"
                rawtext += ")\n\n"
    annotateUMR(rawtext, fn)