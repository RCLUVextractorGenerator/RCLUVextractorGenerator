#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Apr 15 10:20:49 2018

@author: Karthik Vishwambar
"""
#!/usr/bin/python

import re
import glob
import os
import xml.etree.ElementTree as ET
import time
import json
import sys

# List of various token which can be ignored 
TXLtoken = ['id','number','stringlit','charlit','comment','space','newline','upperlowerid','upperid','lowerupperid','lowerid','floatnumber','decimalnumber','integernumber','empty','key','token','srclinenumber','srcfilename','lengthrule','special']
TXLmodifier = ['opt','repeat','list','attr','see','not','push','pop','?','*','+',',',',+',':','~','>','<']    
TXLunparseElement = ['NL','FL','IN','EX','IN_NN','EX_NN','TAB','TAB_NN','SP','SP_NN','SPOFF','SPON']
TXLother =['any','.','^',';']
FilterToken = ['opt','repeat','list','attr','see','not','push','pop','?','*','+',',',',+',':','~','>','<']    

nonterminals = []
root = ET.Element('Feature',remove='false')
parent = root
dictChildParentMap = {}
dictXMLNodecopy = {}

#User Config
with open('config/Pythonconfig.json') as config_data:
    RCLUVConfig = json.load(config_data)


#Function to extract words between the big brackets
def extractWords(pattern):
    start = pattern.find('[')
    if start == -1:
        # modification needed for Error messages
        return ''
    start += 1  # skip the bracket, move to the next character
    end = pattern.find(']', start)
    if end == -1:
        # No closing bracket found after the opening bracket.
        # modification needed for Error messages
        return pattern[start:]
    else:
        return pattern[start:end]


DuplicateNonTerminals = []
ScanningRedefineStmt = False
RedefineNonTerminalBody = []
RedefineNonTerminalHead = ''
hasAltForm = False
#Function to first-scan the grammar and get the non-terminals
def FirstPass_getNonTerminal (strline):
     wordList=''
     global parent
     global DuplicateNonTerminals
     global ScanningRedefineStmt
     global RedefineNonTerminalHead
     global RedefineNonTerminalBody
     global hasAltForm
        
     if re.match('define \w',strline):
         DuplicateNonTerminals=[]
         nonTmnl = strline.replace('define ','')
         nonTmnl = nonTmnl.replace('\n','')
         nonTmnl = nonTmnl.strip()
         parent = root
         if nonTmnl not in nonterminals: 
            nonterminals.append(nonTmnl) 
         child = ET.SubElement(parent, nonTmnl, remove='true')
         dictChildParentMap[child] = parent
         parent = child
         return;
         
     if re.match('redefine \w',strline):
         DuplicateNonTerminals=[]
         ScanningRedefineStmt = True
         nonTmnl = strline.replace('redefine ','')
         nonTmnl = nonTmnl.replace('\n','')
         nonTmnl = nonTmnl.strip()
         if nonTmnl not in nonterminals: 
            nonterminals.append(nonTmnl)
         RedefineNonTerminalHead = nonTmnl
         return;
         
     if ScanningRedefineStmt and strline.find('...') != -1:
         RedefineNonTerminalBody.append('...')
         
     if re.match('.*\[.*\].*',strline) or strline.find('|') != -1:
         if strline.find('|') != -1:
             hasAltForm = True
         strline = strline.replace('\'[','')
         while (re.match('.*\[.*\].*',strline)):
             applyFilter = False
             wordList = extractWords(strline)
             strList = wordList.split(' ')
             for item in strList:
                 if item in FilterToken:
                     applyFilter = True
             for item in strList:
                 if item not in TXLtoken and item not in TXLunparseElement and item not in TXLmodifier and item not in TXLother:
                     if not item.startswith('\'') and item != '':
                         item = item.strip()
                         if(item != ''):
                             while(item[-1] in  TXLmodifier):
                                 item = item[:-1]
                                 applyFilter = True
                         if item not in DuplicateNonTerminals:  
                             if item not in nonterminals:        
                                 nonterminals.append(item)
                             DuplicateNonTerminals.append(item)
                             if not ScanningRedefineStmt:
                                 if applyFilter:
                                     child = ET.SubElement(parent,item, remove='false')
                                 else:
                                     child = ET.SubElement(parent,item, remove='true')    
                                 dictChildParentMap[child] = parent
                             else:
                                 if applyFilter:
                                     RedefineNonTerminalBody.append(item)
                 if item in FilterToken or strline.find('|') != -1 or applyFilter:
                     if ScanningRedefineStmt:
                         RedefineNonTerminalBody.append('ThisIsNotRemovable')
                     else:
                         parent.set('remove','false')
                     
             strline = strline.replace('['+wordList+']','',1)
         if strline.find('|') != -1 or strline.find('\'') != -1:
             if ScanningRedefineStmt:
                 RedefineNonTerminalBody.append('ThisIsNotRemovable')
             else:
                 parent.set('remove','false')
         return;
        

# It is hard to track Parent node for any particular XML node in Python,
# dictChildParentMap Dictionary is used to maintain the Parent and Child relationship of nodes
# Function to maintain dictChildParentMap
def reconstructChildParentMap (node):
    for elenode in node.iter():
        childlist = elenode.getchildren()
        for child in childlist:
            nextLevelChild = child.getchildren()
            newNode = ET.Element(child.tag,remove=child.attrib['remove'])
            elenode.remove(child)
            elenode.append(newNode)
            dictChildParentMap[newNode] = elenode
            if len(nextLevelChild) > 0 :
                for NLChild in nextLevelChild:
                    newNode.append(NLChild)
                    dictChildParentMap[NLChild] = newNode


def childImportant():
    global parent
    if parent.getchildren():
        for child in parent:
            child.set('remove','false')
        
# Feature Extractor Time logger                         
start_time = time.time()
print('Feature-Extractor generating..')

# Path for the input Grammar files
path = RCLUVConfig['RCLUVinput']
# Change all grammar file extension to .grm
for filename in glob.iglob(os.path.join(path, '*.Grm')):
    os.rename(filename, filename[:-4] + '.grm')
for filename in glob.iglob(os.path.join(path, '*.Grammar')):
    os.rename(filename, filename[:-8] + '.grm')
for filename in glob.iglob(os.path.join(path, '*.grammar')):
    os.rename(filename, filename[:-8] + '.grm')

files = glob.glob(os.path.join(path, '*.grm'))

if (len(files) > 1):
    sys.exit('More that one input Grammar loaded in the input stack. Please process a single Language grammar.')
    
for filename in files:
    file = open(RCLUVConfig['RCLUVrefinedTXL'], "r")


    nonterminals = []
    read = False
    for line in file:
        if re.match('define \w',line) or re.match('redefine \w',line):
            read = True
            hasAltForm = False
        if re.match('end define',line):
            read = False 
            if hasAltForm:
                childImportant()
                hasAltForm = False
            
        if re.match('end redefine',line):
            read = False
            if hasAltForm:
                childImportant()
                hasAltForm = False
            ScanningRedefineStmt = False
            
            RootChildren = root.getchildren()
            for rChild in RootChildren:
                if rChild.tag == RedefineNonTerminalHead:
                    ParentNode = rChild
            
            while 'ThisIsNotRemovable' in RedefineNonTerminalBody:
                RedefineNonTerminalBody.remove('ThisIsNotRemovable')
                ParentNode.set('remove','false')
                
            if '...' not in RedefineNonTerminalBody:
                Redefinenode = ParentNode.getchildren()
                for rChild in Redefinenode:
                    ParentNode.remove(rChild)
                    del dictChildParentMap[rChild]
            else:
                RedefineNonTerminalBody.remove('...')
                ParentNode.set('remove','false')
            
            checkList = []
            Redefinenode = ParentNode.getchildren()
            for rChild in Redefinenode:  
                checkList.append(rChild.tag)
            
            for item in RedefineNonTerminalBody:
                if item not in checkList:
                    child = ET.SubElement(ParentNode,item, remove='false')
                    dictChildParentMap[child] = ParentNode
                   
            RedefineNonTerminalHead = ''
            RedefineNonTerminalBody = []
            
        if read :
            FirstPass_getNonTerminal(line)

    file.close()
    # First Pass of Scanning - End
    
  
    #Code generator for the Basic Nonterminals - Begin
    writefilename = filename.replace('.grm','.txl')
    file = open(writefilename, "w+")
    lang = filename.replace(path+'/','')
    langProgram = lang.replace('.grm','')
    file.write('include "'+ lang +'"\n\n')
    
    if RCLUVConfig['OnlyLUV'] == 'False':
        DeConstFuncFile = lang.replace('.grm','')+'DeConstFunction.txl'
        file.write('include "'+ DeConstFuncFile +'"\n\n')
        
    file.write('function main\n')
    file.write('\tmatch [program]\n')
    file.write('\t' + langProgram + 'Program [program]\n\n')
    file.write('\timport TXLinput [stringlit]\n')
    file.write('\t\tconstruct _ [stringlit]\n')
    file.write('\t\tTXLinput [putp "source_file: %"]\n\n')
    
    for nontrml in nonterminals:
        if nontrml not in RCLUVConfig['IgnoreNonTerminals']:
            
            file.write('\tconstruct var'+nontrml+'['+nontrml+'*]\n')
            file.write('\t_ [^ '+langProgram+'Program]\n')
            file.write('\tconstruct _ [number]\n')
            file.write('\t_ [length var'+nontrml+'] [putp"'+nontrml+': %"]\n\n') 
    #Code generator for the Basic Nonterminals - End
    
##RCLUV Begins
    if RCLUVConfig['OnlyLUV'] == 'False':
        Terminals = []
    
        for elenode in root.iter():
            childlist = elenode.getchildren()
            if len(childlist) == 0 and elenode not in Terminals:
                Terminals.append(elenode)
                    
        for node in Terminals:      
            if node.tag not in dictXMLNodecopy.keys():
                for elenode in root.findall('.//'+node.tag):
                    childlist = elenode.getchildren()
                    if len(childlist) > 0 and node.tag not in dictXMLNodecopy.keys(): 
                        Temptree = ET.ElementTree(elenode)
                        Temptree.write('Temp/temp.xml')
                        newTree = ET.parse('Temp/temp.xml')
                        newnode = newTree.getroot()
                        dictXMLNodecopy[node.tag] = newnode
          
        NextLevelTerminals = []        
        for elenode in root.iter():
            childlist = elenode.getchildren()
            if len(childlist) == 0 and elenode not in NextLevelTerminals:
                NextLevelTerminals.append(elenode)
            elif elenode in NextLevelTerminals:
                print('duplicate node ')  
                
        levelNonterminalcount = []     
        levelNonterminalcount.append(len(NextLevelTerminals))   
        LevelRun = 0

        for elenode in root.getchildren():    
            if elenode.attrib['remove'] == 'true':    
                root.remove(elenode)
                del dictChildParentMap[elenode] 
                nonterminals.remove(elenode.tag)     
            
        for Level in range(1,RCLUVConfig['Level']):
            LevelRun = Level
            Terminals = NextLevelTerminals
            NextLevelTerminals = [] 
        
    #MultiLevel Generation - Begin
    #After generating the XML Parse tree, a Non-terminal node having a child node appears only once.
    #Hence each of the leaf nodes in XML is examined to see if there is a node in XML that has child nodes, 
    #If there is, then this leaf node is replaced by the Node with child nodes to grow the Parse Tree in levels
            i=0
            count =0
            for node in Terminals:  
                i = i+1
                #print('Level'+str(Level)+'---'+str(len(Terminals))+'---'+str(i)+'+++'+str(node))
                flag_set = False
                if node.tag in dictXMLNodecopy:
                    flag_set =True
            
                if flag_set :
                    newnode = dictXMLNodecopy[node.tag]
                    parentNode = dictChildParentMap[node]
                    Temptree = ET.ElementTree(newnode)
                    Temptree.write('Temp/temp.xml')
                    newTree = ET.parse('Temp/temp.xml')
                    newnode = newTree.getroot()
                    newnode.set('remove',node.attrib['remove'])
                    parentNode.remove(node)
                    del dictChildParentMap[node]

                    parentNode.append(newnode)
                    dictChildParentMap[newnode] = parentNode
                    reconstructChildParentMap(newnode)
                    if newnode.getchildren():
                        for childNode in newnode.getchildren():
                            NextLevelTerminals.append(childNode) 
                else:
                    if not node.getchildren():
                        NextLevelTerminals.append(node)
        
            levelNonterminalcount.append(len(NextLevelTerminals))
            
        #First Level Generation - End

        listnode = root.getchildren()
        TerminalList = []
        TerminalSet = []
    
        for child in root.iter():
            Xpath = []
            Parentnode = child
            while Parentnode.tag != root.tag:
                if Parentnode.attrib['remove'] == 'false' and Parentnode.tag not in RCLUVConfig['IgnoreNonTerminals']:
                    Xpath.append(Parentnode.tag) 
                Parentnode = dictChildParentMap[Parentnode]
                
            if(len(Xpath) > 1) and Xpath[::-1] not in TerminalSet:
                TerminalSet.append(Xpath[::-1])     
              
#    print(levelNonterminalcount)     
#    print(len(TerminalSet)) 

        
        
    #Code Generation for RCLUV - Begin  
        level = 1 
        strFunctionCal=''
        strFunctionDef=''
        rootNode = []
        rootNodeTXLVariable = {}
        count = 1
        for varel in TerminalSet:
            if varel[0] not in rootNode:
                rootNode.append(varel[0])
                rootNodeTXLVariable[varel[0]] = 'var'+varel[0]

            varname1 = 'var'+str(count)
            varname = 'var'+str(count)
            count = count + 1
            for item in varel:
                varname = varname + '___' + item
                varname1 = varname1 + '_' +item
        
            strFunctionCal = strFunctionCal + '\n\n%'+varname1+'\n\tconstruct ' + varname1 + ' [number]\n'
            strFunctionCal = strFunctionCal + '\t_[countFeature' + varname1 + ' each '+ rootNodeTXLVariable[varel[0]] +'] [putp "'+ varname +': %"]\n'
        
            strFunctionDef = strFunctionDef + 'function countFeature'+ varname1 + ' Ref ['+ varel[0] +']' 
        
            TXLFunDeConstVar='Ref'
            FunDeConstVarCount = 1
            for feature in  varel[1:len(varel)]:
                strFunctionDef = strFunctionDef + '\n\tdeconstruct * [' +feature+ '] ' + TXLFunDeConstVar
                TXLFunDeConstVar = feature +'DeConstVar'+ str(FunDeConstVarCount)
                strFunctionDef = strFunctionDef + '\n\t\t'+TXLFunDeConstVar+' ['+feature +']'
                FunDeConstVarCount = FunDeConstVarCount + 1
        
            strFunctionDef = strFunctionDef +'\n\t'+'replace [number]'+'\n\t\t'+'N [number]'+'\n\t'+'by'+'\n\t\t'+'N [+ 1]'+'\nend function\n\n'

    #Code Generation for RCLUV - End      
        tree = ET.ElementTree(root)
        tree.write(writefilename.replace('.txl','.xml'))
    
        file.write(strFunctionCal)   
    file.write('\nend function')
    file.close()  
    
    if RCLUVConfig['OnlyLUV'] == 'False':    
        file = open(path+'/'+DeConstFuncFile, "w+")  
        file.write(strFunctionDef)
        file.close()       
    
    root.clear()
    config_data.close()
    dictChildParentMap.clear()
    nonterminals.clear()
    dictXMLNodecopy = {}

print('Feature-Extractor generated in ',time.time() - start_time,' time')
    
    


