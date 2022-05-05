import streamApp.Grammar.launchScripts


def writeWord(word) :
    if not word.__eq__('stop') and not word.__eq__('X'):

        if word.__eq__('ecrire'):
            word = 'écrire'

        streamApp.Grammar.launchScripts.phraseInitiale.append(word)

    elif word.__eq__('stop'):
        streamApp.Grammar.launchScripts.phraseInitiale.clear()


