
import os, getpass

def OpenFile( name ) :
    return file( '%s.rtf' % name, 'w' )

class RTF(object):

    def __init__(self, control):
        self.control = control

        twips = 1440
        self.descriptionLeftMargin = int(0.5 * twips)
        self.descriptionRightMargin = int(0.0 * twips)

        self.characterCueLeftMargin = int(2.7 * twips)
        self.characterCueRightMargin = int(1.2 * twips)

        self.parentheticLeftMargin = int(2.1 * twips)
        self.parentheticRightMargin = int(1.6 * twips)

        self.dialogLeftMargin = int(1.5 * twips)
        self.dialogRightMargin = int(1.5 * twips)

    def export(self, event):

        if self.view.selectedIndex in [0, 1]:
            self.exportGraphicNovel()

        elif self.view.selectedIndex in [2, 3]:
            self.exportScreenplay()

    def rtfHeaderData(self):
        return """{\\rtf1\\ansi\\ansicpg1252\\deff0\\deflang3081{\\fonttbl{\\f0\\fnil\\fcharset0 Courier Prime;}}
{\\*\\specscripter generated rtf;}\\viewkind4\\uc1\n"""

    def titlePage(self, f, title, author, contact):
        
        # 53 lines exist for page with Courier Prime, first line exist so we have 52 left
        linesLeft = 52
        
        # this puts the cursor on the 20th line.
        for i in range(19):
            f.write(self.titleParagraph())
        linesLeft -=19
        
        titleLines = title.rstrip().lstrip().split("\n")
        for line in titleLines:
            f.write(self.titleBoldParagraph(line))
            linesLeft -=1
            
        f.write(self.titleParagraph("Written by"))
        linesLeft -=1

        authorLines = author.rstrip().lstrip().split("\n")
        for line in authorLines:
            f.write(self.titleParagraph(line))
            linesLeft -=1
        
        contactLines = []
        if contact:  
            contactLines = contact.rstrip().lstrip().split("\n")
            emptyLineCount = linesLeft -len(contactLines) 
        else:
            emptyLineCount = linesLeft
        
        for i in range(emptyLineCount +1):
            f.write(self.titleParagraph())
            linesLeft -=1

        for line in contactLines:
            f.write(self.contactParagraph(line))
            linesLeft -=1

    def exportScript(self, exportPath, isScreenplay=False):

        if exportPath == "":
            return
    
        f = open(exportPath, "w")

        data = self.rtfHeaderData()
        f.write(data)
        
        title = self.control.currentStory().title
        author = getpass.getuser()

        self.titlePage(f, title, author, contact='')

        sceneNumber = 0
        pageNumber = 0

        for scene in self.control.currentSequence().scenes:

            if not isScreenplay:
                sceneNumber += 1
                sceneHeading = str(sceneNumber) + ". " + scene.title
                f.write(self.sceneParagraph(sceneHeading))

            for page in scene.pages:

                if not isScreenplay:
                    pageNumber += 1
                    pageHeading = "Page " + str(pageNumber)
                    f.write(self.pageParagraph(pageHeading))
                    f.write(self.descriptionParagraph(""))

                panelNumber = 0

                for line in page.lines:

                    if line.tag == 'description':
                        if not isScreenplay:
                            panelNumber += 1
                            panelHeading = "Panel " + str(panelNumber)
                            f.write(self.descriptionParagraph(panelHeading))

                    cn = line.tag

                    if cn in ['description', 'sceneHeading']:
                        f.write(self.descriptionParagraph(line.text))
                        f.write(self.descriptionParagraph(""))

                    elif cn == 'character':
                        f.write(self.characterParagraph(line.text))

                    elif cn == 'parenthetic':
                        f.write(self.parentheticalParagraph(line.text))

                    elif cn == 'dialog':
                        f.write(self.dialogParagraph(line.text))
                        f.write(self.descriptionParagraph(""))


                f.write(self.descriptionParagraph(""))


        f.write("}")
        f.close()

    def descriptionParagraph(self, text=""):
        return """\\pard """ + text + """\\par\\n"""

    def characterParagraph(self, text=""):
        return """\\pard\\li""" + str(self.characterCueLeftMargin) + """\\ri""" + str(self.characterCueRightMargin) + """\\sb60\\sa60 """ + text + """\\par\\n"""

    def dialogParagraph(self, text=""):
        return """\\pard\\li""" + str(self.dialogLeftMargin) + """\\ri""" + str(self.dialogRightMargin) + """\\sb60\\sa60 """ + text + """\\par\\n"""

    def parentheticalParagraph(self, text=""):
        return """\\pard\\li""" + str(self.parentheticLeftMargin) + """\\ri""" + str(self.parentheticRightMargin) + """\\sb60\\sa60 """ + text + """\\par\\n"""
    
    def titleBoldParagraph(self, text=""):
        return """\\pard\\qc\\b """ + text + """\\b0\\par\\n"""
    
    def titleParagraph(self, text=""):
        return """\\pard\\qc """ + text + """\\par\\n"""
    
    def contactParagraph(self, text=""):
        return """\\pard\\qr """ + text + """\\par\\n"""
    
    def pageParagraph(self, text=""):
        return """\\pard\\b """ + text + """\\b0\\par\\n"""
    
    def panelParagraph(self, text=""):
        return """\\pard\\b """ + text + """\\b0\\par\\n"""

    def sceneParagraph(self, text=""):
        return """\\pard\\b """ + text + """\\b0\\par\\n"""

    