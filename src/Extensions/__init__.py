# from template import ExtensionTemplate
# from MwRandomEvents import ExtensionMwRandomEvents
# 
# extensionClasses = [ExtensionTemplate, ExtensionMwRandomEvents] 

import os
import importlib

extensionClasses = []   #empty list

localDir = os.path.dirname(__file__)
localChilds = os.listdir(localDir)
subDirs = []
for f in localChilds:
    if os.path.isdir(os.path.join(localDir, f)):
        subDirs.append(f)

for sd in subDirs:
    try:
        extPackage = importlib.import_module(__name__ + "." + sd)   #results in module names like Extensions.Template
        extensionClasses.append( extPackage.extensionClass )
    except Exception as e:
        print "no valid extension package/folder:", sd, e
        
del localDir,localChilds,subDirs
