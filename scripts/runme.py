from shutil import copyfile
import nuke

def main():
    undo = nuke.Undo()
    undo.begin('GEX prep update')
    copyfile(nuke.root().name(), nuke.root().name() +'.safecopy')
    undo.end

if __name__ == "__main__":
    main()