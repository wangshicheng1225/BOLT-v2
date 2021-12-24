
def generateDefermentForest(DFA, stateNum):
    
    DF = []

    for i in range(stateNum):
        DF.append([])
        for j in range(i + 1, stateNum):
            sameTrans = 0
            for k in range(256):
                if DFA[i][k] == DFA[j][k]:
                    sameTrans = sameTrans + 1
            DF[i].append(sameTrans)

    return DF

def generateDFA(stateNum, transitions):

    DFA = []

    for i in range(stateNum):
        DFA.append([])
        for j in range(256):
            DFA[i].append(0)

    for transition in transitions:
        if isinstance(transition[1], int) == True:
            if transition > 255:
                print("integer is bigger than 255")
                break

            DFA[transition[0]][transition[1]] = transition[2]
        elif isinstance(transition[1], str) == True:
            for ch in transition[1]:
                DFA[transition[0]][ord(ch)] = transition[2]
        elif isinstance(transition[1], tuple) == True:
            if len(transition[1]) != 2 or isinstance(transition[1][0], int) == False or isinstance(transition[1][1], int) == False or transition[1][0] > transition[1][1]:
                print("a tuple with 2 integers is needed")
                break
            
            for index in range(transition[1][0], transition[1][1]+1):
                DFA[transition[0]][index] = transition[2]


    return DFA 

def getRoot(DFA, stateNum):
    maxSelfTransition = -1
    root = 0
    for i in range(stateNum):
        selfTransiton = 0
        for j in range(256):
            if DFA[i][j] == i:
                selfTransiton = selfTransiton + 1
        if selfTransiton > maxSelfTransition:
            maxSelfTransition = selfTransiton
            root = i

    return root

def getMaximumSpanningTree(stateNum, DF, root):
    edges = []
    fuset = []
    graph = []
    visited = []

    for i in range(stateNum):
        visited.append(0)

    for i in range(stateNum):
        graph.append([])
        for j in range(stateNum):
            graph[i].append(0)

    for i in range(stateNum):
        fuset.append(i)
        for j in range(stateNum-i-1):
            edges.append([-DF[i][j], i, j+i+1])
    edges.sort()

    'print edges'

    for edge in edges:
        # print getAncestor(fuset, edge[1])
        # print getAncestor(fuset, edge[2])
        # print '*****'
        if getAncestor(fuset, edge[1]) != getAncestor(fuset, edge[2]):
            graph[edge[1]][edge[2]] = graph[edge[2]][edge[1]] = 1
            if getAncestor(fuset, edge[1]) < getAncestor(fuset, edge[2]):
                fuset[getAncestor(fuset, edge[2])] = getAncestor(fuset, edge[1])
            else:
                fuset[getAncestor(fuset, edge[1])] = getAncestor(fuset, edge[2])

    'print graph'

    visited[root] = 1
    tree = getTreeWithRoot(stateNum, graph, root, visited)

    return tree
    

def getTreeWithRoot(nodeNum, graph, root, visited):
    tree = []
    children = []
    tree.append(root)
    for i in range(nodeNum):
        if graph[root][i] == 1 and visited[i] == 0:
            children.append(i)
            visited[i] = 1
    
    if len(children) == 0:
        return tree

    for child in children:
        tree.append(getTreeWithRoot(nodeNum, graph, child, visited))

    return tree

def getAncestor(fuset, index):
    while fuset[fuset[index]] != fuset[index]:
        fuset[index] = fuset[fuset[index]]

    return fuset[index]

def generateShadowCode(defermentTree, stateInfo):
    stateList = []

    if len(defermentTree) == 1:
        return 

    stateList.append([stateInfo[defermentTree[0]]['weight'], defermentTree[0]])
    for i in range(1, len(defermentTree)):
        generateShadowCode(defermentTree[i], stateInfo)
        stateList.append([stateInfo[defermentTree[i][0]]['weight'], defermentTree[i][0]])
    stateList.sort()
    while len(stateList) != 1:
        lnode = stateList.pop(0)
        rnode = stateList.pop(0)
        stateList.append([max(lnode[0], rnode[0]) + 1, [ lnode[1], rnode[1] ] ])
        stateList.sort()
    
    stateInfo[defermentTree[0]]['weight'] = stateList[0][0]

    # print '*****'
    # print stateList[0][1]
    # print '*****'
    updateInfoWithHufTree(stateInfo, stateList[0][1], defermentTree[0], '', defermentTree)

    return

def updateInfoWithHufTree(stateInfo, hufTree, fatherNode, prefix, defermentTree):
    if isinstance(hufTree, int):
        if hufTree == fatherNode:
            stateInfo[fatherNode]['localCode'] = prefix
        else:
            subtree = findSubTreeByRoot(defermentTree, hufTree)
            iteratedUpdate(subtree, prefix, stateInfo)
        return
    else:
        for i in range(2):
            updateInfoWithHufTree(stateInfo, hufTree[i], fatherNode, prefix+'%d'%i, defermentTree)
        return

    '''if isinstance(hufTree[1], int):
        if hufTree[1] == fatherNode:
            stateInfo[fatherNode]['localCode'] = prefix
        else:
            iteratedUpdate(defermentTree, hufTree[1]])
    else:
        updateInfoWithHufTree(stateInfo, hufTree[1], fatherNode, '1'+prefix)'''

def findSubTreeByRoot(tree, root):
    if tree[0] == root:
        return tree
    elif len(tree) == 1:
        return None
    else:
        for i in range(1, len(tree)):
            res = findSubTreeByRoot(tree[i], root)
            if res != None:
                return res
        return None

def iteratedUpdate(tree, prefix, stateInfo):
    stateInfo[tree[0]]['globalCode'] = prefix + stateInfo[tree[0]]['globalCode']

    if len(tree) == 1:
        return
    else:
        for i in range(1, len(tree)):
            iteratedUpdate(tree[i], prefix, stateInfo)


def getSpanningDeferTree(DFA):
    stateNum = len(DFA[0])
    transitions = []
    for i in range(len(DFA[1])):
        transitions.append([DFA[1][i][0], DFA[1][i][1], DFA[1][i][2]])

    newDFA = generateDFA(stateNum, transitions)

    DF = generateDefermentForest(newDFA, stateNum)
    print("SRG")
    print(DF)

    root = getRoot(newDFA, stateNum)
    # print root
    # print "root: ", root
    tree = getMaximumSpanningTree(stateNum, DF, root)
    
    return tree

def getSCIDWithDFA(DFA):
    stateNum = len(DFA[0])

    transitions = []
    for i in range(len(DFA[1])):
        transitions.append([DFA[1][i][0], DFA[1][i][1], DFA[1][i][2]])

    newDFA = generateDFA(stateNum, transitions)

    DF = generateDefermentForest(newDFA, stateNum)
    # print DF

    root = getRoot(newDFA, stateNum)
    # print root

    tree = getMaximumSpanningTree(stateNum, DF, root)
    #print tree

    stateInfo = [{"globalCode" : '', 'localCode' : '', 'weight' : 0} for i in range(stateNum)]
    generateShadowCode(tree, stateInfo)
    # print stateInfo
    
    shadowCode = []
    shadowCodeLen = stateInfo[tree[0]]["weight"]
    for i in range(stateNum):
        shadowCode.append(stateInfo[i]["globalCode"] + (shadowCodeLen - len(stateInfo[i]["globalCode"])) * '*')
    # print shadowCode
    IDCode = []
    for i in range(stateNum):
        IDCode.append(stateInfo[i]["globalCode"] + stateInfo[i]["localCode"] + (shadowCodeLen - len(stateInfo[i]["globalCode"]) - len(stateInfo[i]["localCode"]))*'0')
    
    # templst = []
    # templst.append(shadowCode)
    # templst.append(IDCode)
    return (shadowCode,IDCode)

def getSCIDWithNFA(NFA, defer_tree):
    stateNum = len(NFA[0])

    # transitions = []
    # for i in range(len(DFA[1])):
    #     transitions.append([DFA[1][i][0], DFA[1][i][1], DFA[1][i][2]])

    # newDFA = generateDFA(stateNum, transitions)

    # DF = generateDefermentForest(newDFA, stateNum)
    # # print DF

    # root = getRoot(newDFA, stateNum)
    # # print root

    # tree = getMaximumSpanningTree(stateNum, DF, root)
    #print tree

    stateInfo = [{"globalCode" : '', 'localCode' : '', 'weight' : 0} for i in range(stateNum)]
    generateShadowCode(defer_tree, stateInfo)
    # print stateInfo
    
    shadowCode = []
    shadowCodeLen = stateInfo[defer_tree[0]]["weight"]
    for i in range(stateNum):
        shadowCode.append(stateInfo[i]["globalCode"] + (shadowCodeLen - len(stateInfo[i]["globalCode"])) * '*')
    # print shadowCode
    IDCode = []
    for i in range(stateNum):
        IDCode.append(stateInfo[i]["globalCode"] + stateInfo[i]["localCode"] + (shadowCodeLen - len(stateInfo[i]["globalCode"]) - len(stateInfo[i]["localCode"]))*'0')
    
    # templst = []
    # templst.append(shadowCode)
    # templst.append(IDCode)
    return (shadowCode,IDCode)

def getShadowCodeWithNFA(NFA,defer_tree):
    stateNum = len(DFA[0])

    # transitions = []
    # for i in range(len(DFA[1])):
    #     transitions.append([DFA[1][i][0], DFA[1][i][1], DFA[1][i][2]])

    # newDFA = generateDFA(stateNum, transitions)

    # DF = generateDefermentForest(newDFA, stateNum)
    # # print DF

    # root = getRoot(newDFA, stateNum)
    # # print root

    # tree = getMaximumSpanningTree(stateNum, DF, root)
    # #print tree

    stateInfo = [{"globalCode" : '', 'localCode' : '', 'weight' : 0} for i in range(stateNum)]
    generateShadowCode(defer_tree, stateInfo)
    # print stateInfo
    
    shadowCode = []
    shadowCodeLen = stateInfo[defer_tree[0]]["weight"]
    for i in range(stateNum):
        shadowCode.append(stateInfo[i]["globalCode"] + (shadowCodeLen - len(stateInfo[i]["globalCode"])) * '*')
    # print shadowCode
    
    return shadowCode

def getShadowCodeWithDFA(DFA):
    stateNum = len(DFA[0])

    transitions = []
    for i in range(len(DFA[1])):
        transitions.append([DFA[1][i][0], DFA[1][i][1], DFA[1][i][2]])

    newDFA = generateDFA(stateNum, transitions)

    DF = generateDefermentForest(newDFA, stateNum)
    # print DF

    root = getRoot(newDFA, stateNum)
    # print root

    tree = getMaximumSpanningTree(stateNum, DF, root)
    #print tree

    stateInfo = [{"globalCode" : '', 'localCode' : '', 'weight' : 0} for i in range(stateNum)]
    generateShadowCode(tree, stateInfo)
    # print stateInfo
    
    shadowCode = []
    shadowCodeLen = stateInfo[tree[0]]["weight"]
    for i in range(stateNum):
        shadowCode.append(stateInfo[i]["globalCode"] + (shadowCodeLen - len(stateInfo[i]["globalCode"])) * '*')
    # print shadowCode
    
    return shadowCode

if __name__ == "__main__":
    transitions = [[0, 'abcdefghijklmno', 1], [1, 'b', 1], [1, 'acdefghijklmno', 2], [2, 'bc', 1], [2, 'adefghijklmno', 2]]
    
    DFA = generateDFA(3, transitions)
    print(DFA[0])
    print(DFA[1])
    print(DFA[2])


    DF = generateDefermentForest(DFA, 3)
    print("Deferment Forest ")
    print(DF)
    print("Deferment Forest End")

    root = getRoot(DFA, 3)
    print(root)

    tree = getMaximumSpanningTree(3, DF, root)
    print("TREE")
    print(tree)

    stateInfo = [{"globalCode" : '', 'localCode' : '', 'weight' : 0} for i in range(7)]
    tree = [0, [1], [2, [4]], [3, [5], [6]]]
    generateShadowCode(tree, stateInfo)
    print(stateInfo)
