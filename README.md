![](http://specscripter.com/logo.png "")

<h3>Simple. Fast. Organized.</h3>

Diego's goals are to be a simple, fast, organized, unobtrusive scriptwriting software for Graphic Novel Writers. Diego seconds as [spec script](https://en.wikipedia.org/wiki/Spec_script) software as well.

Diego has traded feature bloat for simplicity. Only features that are necessary to get the job done are added. Diego's design centers around keeping the writers hands on the keyboard. Keyboard shortcuts replace the common interface cluttered with buttons and menus and sub-menus.

Diego does not need to be saved, it saves each document on shutdown of the app. Each Scene contains it's own history. History is persistent, which means it is saved along with the document.

When Diego saves, three documents are created: the Diego document, an RTF for extra tweaking, and a PDF.

<b>Graphic Novel Mode</b>

![Graphic Novel Mode](http://specscripter.com/graphicNovelMode.png "Graphic Novel Mode")

<b>Screenplay Mode</b>

![Screenplay Mode](http://specscripter.com/screenplayMode.png "Screenplay Mode")

<b>System Requirements</b>

Linux Operationing System

Python 2.7

Pygtk 3.14.15 + installed.

<b> Optional</b>

<p><a href="https://pypi.python.org/pypi/marisa-trie">marisa-trie</a> marisa-trie is needed for spell checking</p>

<p><a href="https://www.libreoffice.org/download/libreoffice-fresh/">LibreOffice</a> LibreOffice is needed to create pdf's</p>

<p><a href="http://quoteunquoteapps.com/courierprime/">Courier Prime Font</a> Courier Prime is needed for correct formatting in viewing and exporting.</p>

<h4>Two Example Scripts are included:</h4>
Hansel And Gretal - Screenplay directly adapted from the original story.

Salem - Sample pages from a graphic novel.

<h2>How To Use Diego</h2>

<b>How To Run The App</b>

python app.py

<b>Create a Story, Scene or Page</b>

Select an item in the Story, Scene or Page view. Hit Enter Key to create new item.

<b>Remove a Story from the Story View (Just removes from view, does not Delete)</b>

Select an item in the Story View. Hit Delete key.

<b>Delete a Scene or Page</b>

Select an item in the Scene or Page View. Hit Delete key. Deleting a Scene will delete all pages contained within it.

<b>How to Format A Line as Description, Character, Parenthetic or Dialog</b>

If the line is empty, press the Spacebar. If the line has text, then place the cursor at the beginning of the line and hit Spacebar.

<b>Completion</b>

Tab key turns completion on.

Interactive Usage: Type a prefix then press the Tab key to see candidate suffixes, then...

- Hitting Return key will accept current suffix, and turns completion off.

- Hitting Space key will accept current suffix, places a space after it and turns completion off.

- Hitting Delete key will remove current suffix and turn completion off.

- Hitting Escape key will remove current suffix, and resets completion to first suffix.

<b>Add Character To Story</b>

Type character name in the editor. Select the name. Right click and choose "Add Name to Characters"

<b>Name/Rename A Scene Title</b>

Double click the scene title in the Scene View. Type in new name.

<b>Find And Replace</b>

Control + r

<b>Save Story</b>

Control + s.  Also creates an rtf and pdf if you have Libre Office installed.

<b>Save Story As</b>

Rename by double clicking the Story Title in Story View. <i>Optionally, Control + Shift + s.</i>

<b>Open Story</b>

Control + o

<b>Prepend A New Scene/Page</b>

Select the Scene or page in which you want the Scene/Page to be inserted before.  Hold down Control and press enter.

<b>Increase/Decrease Font Size</b>

Place the cursor in the editor you want to resize font. Hold down Control and press the plus or minus keys.

<b>Toggle Story/Scene Numbering</b>

Hold down Control and press #.

<b>Find In Story/Scene/Page</b>

Go to Story, Scene, or Page View. Type single word in Find Entry.

<b>Screenplay Mode</b>

Right click over the text editor. Choose Screenplay Mode from the popup menu. In Screenplay mode, Locations and Times will now complete.

<b>Set Author/Contact Information</b>

Press Atl + i, this information will be inserted into rtf and pdfs.

<b>Move A Scene/Page</b>

Select the Scene or Page to be moved in the Scene/Page View.  Hold down Control key and press up or down arrow key.

<b>Clear History</b>

Control + Delete

<b>Set Backup Disk</b>

Select Set Backup Disk from Right Click Menu.

<b>Minimal View</b>

Press Escape Key

<b>Full Screen</b>

Press F11

<b>Scroll Scene/Page</b>

Press Page Up/Down Key

