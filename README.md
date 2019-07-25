# AMR/UMR annotation tools

These are two extraordinarily simplistic tools for building AMR and UMR annotations.  

Both tools require the pysimpleGUI package, installed with:

```pip install PySimpleGUI```

From there, you should be able to directly start to annotate files!  

UMR Annotator
-------------

The UMR annotator is a general toolkit for annotating documents.  It starts with an existing list of AMRs (shown on the left panel) and you build up the UMR (shown on the right).  

```python umr-annotator.py annotations/umr/LittlePrince_ch1_34amrs.txt```

If you point it at a list of AMRs (with IDs, etc.) it will pre-seed the start of an annotation.  Add a second argument ```unm``` or ```cu``` to tell it whether to start with Tim's unified graph representation or the UNM modal dependency graph assumptions.  As with everything: email me or open an issue for tweaks to that (or submit a PR!) . 



#### Annotation Method


Most annotation uses the same commands as the ISI AMR Editor.  You may introduce a new concept with ```<variable> <relation> <concept>```, may add a new relation with ```<variable> <relation> <variable2>```, and may move a variable by appending ```-``` after the variable. The main addition for UMR is the ```!``` operator, and the ```focus=X``` command.

You may use ```focus=<sentence number>``` to shift the focus of the UMR -- where 'focus' here just means which sentence-level AMR were are referring to (shown in black instead of grey).  This allows you to link to that AMR without any complicated universal references.  You may then use the command ```<variable in umr> <relation> <variable in AMR under focus>!``` .  This will then copy over the concept from the AMR in focus, will add it to the UMR, and will also automatically add a ```:doclink``` relation to that new UMR node, so that we actually have hard link to that node in that AMR. 

AMR Annotator
-------------

The AMR annotator is under construction, and currently takes files in toolbox format.  That's a weird choice, I know, but the ultimate goal is to allow people to port information over from existing morphological analysis -- and I assume that for many languages, that means making "amr concepts" just copied from morphological analysis line. There is an ugly ugly script (txt2amrinput.py, which requires nltk packages) which prepares a normal text file for annotation (arg1 = input, arg2 =output). 

To run the main annotation tool, just call ```python amr-editor.py``` and it will open a filename prompt. Click on the file to annotate -- it will automatically check for annotation files, for now.  It works like the normal AMR Editor online does, but anything in the ```\mb``` line will be split up and given a code for each value (as "morphcodes'), which you can then add with a shortcut.  For example, a morphological line form the arapaho data has "# ::morphcodes [0]hinen [1]no' [2]he'ih [3]noohob [4]eeno' [5]honoh'oehiho' [6]hihii3iihi' [7]hi [8]yeih' [9]inoo" -- "@5" can now be used as a shortcut for "honoh'oehiho'", and "@6" as a shortcut for "hihii3iihi'".  That won't fix the issue of hard-to-type languages, but hopefully will help.


