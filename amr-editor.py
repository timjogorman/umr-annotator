import PySimpleGUI as sg
import penman, string, sys, os, json
from amranno import *


class AnnotationFile:
    def __init__(self, rawdictionary, filename):
        self.filename = filename
        self.all_sentences = rawdictionary
        if os.path.exists(filename+".in-progress.txt"):
            self.all_amrs ={}
            for each_amr in open(filename+".in-progress.txt").read().strip().split("\n\n"):
                its_id = [x for x in each_amr.split("\n") if "# ::id" in x][0].replace("# ::id",'').strip()
                raw_amr = "\n".join([x for x in each_amr.split("\n") if not "# ::id" in x])
                self.all_amrs[its_id] = raw_amr

        else:
            self.all_amrs = {}        
        
    def annotate(self, start=0):
        while True:
            command = self.annotateAMR(self.all_sentences[start], start)
            if command == 'exit':
                return None
            if command.lower() == 'next':
                start +=1
            if command.lower().startswith('goto'):
                start = int(command.lower().replace("goto","").strip())

    def annotateAMR(self, rawjson, amrid):
        rawid = self.all_sentences[amrid]['id']
        sg.SetOptions(background_color='#FFFFFF', element_background_color='#FFFFFF', text_element_background_color='#FFFFFF',input_elements_background_color='#FFFFFF')

        sgt = [[sg.Text('', size=(800, 500), key='_OUTPUT_')]]
        some_status = [[sg.Text('', size=(800, 50), key='_TRUTH_')]]
        
        display_box = sg.Column(sgt,
            size=(800, 500),
            scrollable=True)
        comment_box = sg.Column(some_status,
            size=(400, 600),
            scrollable=True)
        
        layout = [[sg.Text("sentence "+str(amrid+1)+" of "+str(len(self.all_sentences))+"\n"+"\n".join(rawjson['raw']), size=(80,20), key='_RAW_')],
                  [display_box, comment_box],
                  [sg.Input(key='_IN_')],
                  [sg.Text('', size=(10,1), key='_STATUS_')],
                  [sg.Button('Show', bind_return_key=True), sg.Button('Exit')]]
        window = sg.Window('Make an AMR', layout, resizable=True).Finalize()
        its_amr = None
        if rawid in self.all_amrs:
            its_amr = AnnotationAMR(self.all_amrs[rawid])
        amr_stack = []
        if its_amr is not None:
            window.Element('_OUTPUT_').Update(str(its_amr.amr))
        while True: 
            event, values = window.Read()
            if values['_IN_'].strip() == 'bail':
                return "exit"
            if event is None or event == 'Exit' or values['_IN_'].strip() == 'exit':
                self.all_amrs[rawjson['id']] = str(its_amr.amr)
                didsave = False
                with open(self.filename+".in-progress.txt",'w') as openfile:
                    for its_id in self.all_amrs:
                        openfile.write("# ::id "+its_id+"\n")
                        openfile.write(self.all_amrs[its_id]+"\n\n")
                        didsave=True
                return "exit"
            if values['_IN_'].strip() == 'NEXT':
                self.all_amrs[rawjson['id']] = str(its_amr.amr)
                didsave = False
                with open(self.filename+".in-progress.txt",'w') as openfile:
                    for its_id in self.all_amrs:
                        openfile.write("# ::id "+its_id+"\n")
                        openfile.write(self.all_amrs[its_id]+"\n\n")
                        didsave=True
                return "next"
            if values['_IN_'].strip().startswith('GOTO'):
                return values['_IN_'].strip()
            status = ''
            if its_amr is not None:
                amr_stack.append(str(its_amr.amr))
            while len(amr_stack) > 20:
                amr_stack.pop(0)
            if its_amr is None and len(str(values['_IN_'].strip()).split(" ")) == 1:
                concept = values['_IN_']
                if concept.startswith("@"):
                    if concept.strip().strip("@").isdigit() and str(concept.strip().strip("@")) in rawjson['map']:
                        concept = rawjson['map'][str(concept.strip().strip("@"))]

                val= firstletter(concept)+"1"

                try:
                    its_amr = AnnotationAMR("("+val +"/"+concept+")")
                except:
                    status = "error in starting AMR"
            elif its_amr is None and "(" in values['_IN_']:
                try:
                    its_amr = AnnotationAMR(values['_IN_'])
                except:
                    status = "error in starting AMR"
            elif "focus=" in values['_IN_']:
                val = values['_IN_'].split("focus=")[1].strip()
                umrf.focus = int(val)
            elif "undo" == values['_IN_'].strip():
                amr_stack.pop()
                its_amr.amr = penman.decode(amr_stack.pop())
            elif "addsense" in values['_IN_'].strip() and len(values['_IN_'].strip().split(" ")) == 3:
                __, variable, senselabel = values['_IN_'].strip().split(" ")
                its_amr.addsense(variable, senselabel)
            elif "save" == values['_IN_'].strip():
                self.all_amrs[rawjson['id']] = str(its_amr.amr)
                didsave = False
                with open(self.filename+".in-progress.txt",'w') as openfile:
                    for its_id in self.all_amrs:
                        openfile.write("# ::id "+its_id+"\n")
                        openfile.write(self.all_amrs[its_id]+"\n\n")
                        didsave=True

                if didsave:
                    status ="successfully saved"
                else:
                    status ="failed to save"
            elif "@" in values['_IN_']:
                head, relation, concept= values['_IN_'].strip().split(" ")
                if concept.startswith("@"):
                    if concept.strip().strip("@").isdigit() and str(concept.strip().strip("@")) in rawjson['map']:
                        concept = rawjson['map'][str(concept.strip().strip("@"))]
                q = its_amr.load_update(" ".join([head, relation, concept]))

                if not q:
                    status = "could not parse "+" ".join([head, relation, concept])

            elif values['_IN_'].startswith("renamerel"):
                __, head, relation, target, newrelation = values['_IN_'].strip().split(" ")
                its_amr.add_reentrancy(head, newrelation, target)    
                its_amr.delete_relation(head, relation, target)
            elif values['_IN_'].startswith("del") and len(values['_IN_'].strip().split(" ")) ==2:
                its_amr.delete_variable(values['_IN_'].strip().split(" ")[1])
            else:
                q = its_amr.load_update(values['_IN_'])
                if not q:
                    status = "could not parse "+values['_IN_']
            if event == 'Show':
                if its_amr is not None:
                    values['_IN_'] = ''
                    window.Element('_IN_').Update('')
                    window.Element('_STATUS_').Update(status)
                    window.Element('_OUTPUT_').Update(str(its_amr.amr))
        window.Close()

def load_discseg(rawf):
    ongoing = {"id":None,"map":{},"raw":None}

    test_txt = []
    test_mb = []
    test_rawtexts = rawf
    rf = [x for x in rawf.strip().split("\n") if "ref" in x][0]
    mb = [x for x in rawf.split("\n") if x.startswith('\mb')]
    for eachmorphlist in mb:
        while "  " in eachmorphlist:
            eachmorphlist = eachmorphlist.replace("  "," ")
        test_mb += [x.strip("-") for x in eachmorphlist.replace("\mb","").strip().split(" ") if not x == '-']
    outputs=  []
    for j in rawf.split("\n"):
        if j.startswith("\ref"):
            outputs.append(j.replace("\ref", "# ::id ").strip("\n"))
        else:
            if len(j) > 0 and j[0]=='\\':

                outputs.append("# ::"+j[1:].strip("\n"))
    convbox = {str(xid):x for xid, x in enumerate(test_mb)}
    
    ongoing['id'] = [x for x in outputs if "# ::ref" in x][0].replace("# ::ref",'').strip()
    
    e = " ".join(["["+str(xid)+"]"+x for xid, x in enumerate(test_mb)])
    outputs.append("# ::morphcodes "+e)
    ongoing['raw'] = outputs
    ongoing['map'] = convbox
    return ongoing
def igt2json(filename):
    e = []
    for discseg in open(filename).read().split("\n\n"):
        print("-------------------")
        if discseg.strip() == '':
            continue
        s = load_discseg(discseg)        
        print(s)
        e.append(s)
    return e

if __name__ == "__main__":


    layout = [[sg.Text('Filename')],
                     [sg.InputText(), sg.FileBrowse()],
                     [sg.Submit(), sg.Cancel()]]

    event, values = sg.Window('Get filename example', layout).Read()

    source_filename = values[0] 
    rawfile = igt2json(source_filename)
    af = AnnotationFile(rawfile, source_filename)

    af.annotate(0)