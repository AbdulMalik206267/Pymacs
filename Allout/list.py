#!/usr/bin/env python
# -*- coding: Latin-1 -*-
# Copyright � 2001, 2002, 2003 Progiciels Bourbeau-Pinard inc.
# Fran�ois Pinard <pinard@iro.umontreal.ca>, 2001.

"""\
Lorsque ACTION est `list', ce programme reformatte le fichier un peu mieux,
en vue de l'examen visuel ou de l'impression.  Nous avons alors:

Usage: allout list [OPTION]... [FICHIER]

   -a             Produire un format `allout' plut�t qu'un format `listing'
   -s S�LECTION   Limiter le traitement au sous-arbre S�LECTION

FICHIER contient le fichier `allout' � lire, entr�e standard si non fourni.

L'option `-a' restitue un fichier `allout' sur la sortie.

L'option `-s' introduit une liste de nombres s�par�s par des points.  Ces
nombres d�crivent un parcours de s�lection d'un sous-arbre par la s�lection
successive d'un embranchement � chaque niveau.  � chaque niveau, le nombre 0
repr�sente la t�te du niveau, les nombres 1 et suivants repr�sentent les
branches compt�es � partir de la premi�re, les nombres -1 et pr�c�dents
repr�sentent les branches compt�es � partir de la derni�re.  Cette s�lection
s'effectue sur l'arbre apr�s les simplifications d�crites plus haut.
"""

import sys

class Main:
    def __init__(self):
        self.allout = False
        self.selection = []

    def main(self, *arguments):
        self.allout = False
        self.selection = []
        import getopt
        options, arguments = getopt.getopt(arguments, 'as:')
        for option, value in options:
            if option == '-a':
                self.allout = True
            elif option == '-s':
                self.selection = map(int, value.split('.'))
        # Lire le fichier en format `allout'.
        import allout
        if len(arguments) == 0:
            structure = allout.read()
        elif len(arguments) == 1:
            structure = allout.read(arguments[0])
        else:
            raise allout.UsageError, "Trop d'arguments."
        # Choisir la sous-branche d�sir�e.
        for branche in self.selection:
            structure = structure[branche]
        # Imprimer la liste r�sultante.
        if self.allout:
            write(structure)
        else:
            write_listing(structure)

main = Main().main

def write(structure, output=sys.stdout.write):
    # Transformer l'arbre STRUCTURE en un fichier `allout'.  Le r�sultat est
    # �crit sur OUTPUT, qui doit �tre une fonction d'�criture ou encore, le
    # nom d'un fichier � cr�er.
    if isinstance(output, str):
        write_recursive(structure, file(output, 'w').write, 0)
    else:
        write_recursive(structure, output, 0)

def write_recursive(structure, write, level):
    if isinstance(structure, str):
        write('%*s %s\n' % (level, '', structure))
        return
    if level == 0:
        write('* %s\n' % structure[0])
    elif level == 1:
        write('.. %s\n' % structure[0])
    else:
        write('.%*s %s\n' % (level, '.:,;'[(level-1) % 4], structure[0]))
    for branch in structure[1:]:
        write_recursive(branch, write, level+1)

def write_listing(structure, output=sys.stdout.write):
    # Transformer l'arbre STRUCTURE en une liste destin�e � �tre lue par un
    # humain, utilisant une marge blanche croissante, et des lignes
    # blanches, pour souligner l'arboresence.  Le r�sultat est �crit sur
    # OUTPUT, qui doit �tre une fonction d'�criture ou encore, le nom d'un
    # fichier � cr�er.
    if isinstance(output, str):
        write_listing_recursive(structure, file(output, 'w').write, 0, False)
    else:
        write_listing_recursive(structure, output, 0, False)

def write_listing_recursive(structure, write, level, spacing):
    # SPACING est True � l'entr�e si la structure pr�c�dente s'imprimait sur
    # plusieurs lignes, et la valeur de cette fonction est True pour
    # indiquer que STRUCTURE a requis plus d'une ligne pour s'imprimer.
    if spacing or (isinstance(structure, list) and len(structure) > 1):
        write('\n')
    write('  ' * level)
    if isinstance(structure, str):
        write(structure)
        write('\n')
        return False
    write(structure[0])
    write('\n')
    spacing = False
    for element in structure[1:]:
        spacing = write_listing_recursive(element, write, level+1, spacing)
    return len(structure) > 1

if __name__ == '__main__':
    main(*sys.argv[1:])
