#!/usr/bin/env python
# -*- coding: Latin-1 -*-
# Copyright � 2001, 2002, 2003 Progiciels Bourbeau-Pinard inc.
# Fran�ois Pinard <pinard@iro.umontreal.ca>, 2001.

"""\
Un fichier `allout', pour lequel existe un mode Emacs, permet de repr�senter
une organisation hi�rarchique de l'information contenue, avec la possibilit�
d'un court libell� au sommet de chaque hi�rarchie ou sous-hi�rarchie.  Le
fichier utilise des marques sp�ciales pour marquer la structure, soit `*'
compl�tement � gauche d'une ligne pour marquer le d�but d'une hi�rarchie
englobante, soit `.' � gauche d'une ligne, suivi d'un nombre arbitraire de
blancs et de l'un des caract�res `*+-@.:,;', pour marquer le d�but d'une
hi�rarchie plus imbriqu�e, l'imbrication �tant d'autant plus importante que
le caract�re `*+-@.:,;' est plus � droite.  La marque doit �tre le dernier
caract�re sur sa ligne, ou encore, �tre suivie d'au moins un caract�re blanc
puis d'un libell� associ� � la hi�rarchie introduite par cette marque.
Toute ligne n'introduisant pas de marque est une ligne de texte associ�e �
l'�l�ment hi�rarchique le plus r�cemment introduit.

Ce programme ajoute quelques interpr�tations particuli�res � un fichier
`allout' tel que d�fini dans Emacs.  Pour permettre � un fichier d'utiliser
plusieurs hi�rarchies successivement introduites par une marque `*', un
texte qui pr�c�derait la premi�re marque `*' est consid�r� comme
super-englobant, et la toute premi�re ligne non-blanche de ce texte pr�fixe
est alors le libell� associ� � cette hi�rarchie super-englobante.  Dans
toutes les hi�rarchies, sont �limin�es les lignes blanches pr�fixes ou
suffixes, les imbrications superflues (pas de libell� et un seul �l�ment),
et une marge gauche commune � toutes les lignes de texte d'un m�me niveau.

Report bugs or suggestions to Fran�ois Pinard <pinard@iro.umontreal.ca>.
"""

import sys

def read(input=sys.stdin):
    # Lire INPUT, qui est soit un fichier d�j� ouvert, soit le nom d'un
    # fichier � lire, puis retourner un arbre repr�sentant la structure
    # `allout' de ce fichier, ou None dans le cas d'un fichier vide.
    # L'arbre produit est une liste contenant r�cursivement d'autres listes.
    # Chaque liste d�bute par une cha�ne donnant le libell� d'un noeud, et
    # contient ensuite dans l'ordre une cha�ne par ligne ordinaire dans ce
    # noeud ou une sous-liste pour un sous-noeud dans ce noeud.

    # LEVEL vaut 0 pour la hi�rarchie super-englobante, 1 pour la hi�rarchie
    # `*', 2 pour la hi�rarchie `..', etc.  STACK[LEVEL] contient la liste
    # des hi�rarchies tout-�-fait compl�t�es au niveau LEVEL.  Si
    # STACK[LEVEL+1] existe, STACK[LEVEL] devra n�cessairement recevoir un
    # nouvel �l�ment au plus tard � la rencontre de la fin de fichier.

    def collapse():
        # Rapetisser (ou allonger) la pile STACK pour lui donner exactement
        # la longueur LEVEL, tout en d�clarant que les structures empil�es
        # au-del� ont termin� leur croissance: on peut donc imm�diatement
        # imbriquer ces structures dans l'arbre en construction.
        while len(stack) < level:
            stack.append([''])
        while len(stack) > level:
            structure = stack.pop()
            while len(structure) > 1 and structure[-1] == '':
                del structure[-1]
            if len(structure) == 2 and structure[0] == '':
                structure = structure[1]
            else:
                margin = None
                for line in structure[1:]:
                    if isinstance(line, str) and line:
                        count = re.match(' *', line).end(0)
                        if margin is None or count < margin:
                            margin = count
                if margin is not None:
                    for counter in range(1, len(structure)):
                        line = structure[counter]
                        if isinstance(line, str) and line:
                            structure[counter] = line[margin:]
            stack[-1].append(structure)

    if isinstance(input, str):
        input = file(input)
    import re
    stack = []
    for line in input:
        match = re.match(r'(\*|\. *[-*+@.:,;])', line)
        if match:
            level = match.end(0)
            collapse()
            stack.append([line[level:].strip()])
        elif stack:
            line = line.rstrip()
            if line or len(stack[-1]) > 1:
                stack[-1].append(line)
        else:
            line = line.strip()
            if line:
                stack.append([line])
    level = 1
    collapse()
    if len(stack[0]) == 2 and stack[0][0] == '':
        stack[0] = stack[0][1]
    return stack[0]
