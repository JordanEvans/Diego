# Diego

<h3>Simple. Fast. Organized.</h3>

Diego's goals are to be a simple, fast, organized, unobtrusive scriptwriting software for Graphic Novel Writers. Diego seconds as specscript software as well.

Diego has traded feature bloat for simplicity. Only features that are necessary to get the job done are added. Diego's design centers around keeping the writers hands on the keyboard. Keyboard shortcuts replace the common interface cluttered with buttons and menus and sub-menus.

Diego does not need to be saved, it saves each document on shutdown of the app. History is infinite, but can be cleared via right click. A white background means you are treading new ground. A gray background means you have undone in this area. Blue means you have saved this area and have not undone in that area. When Diego saves, three documents are created: the Diego document, an RTF for extra tweaking, and a PDF.

<b>Graphic Novel Mode</b>

![Graphic Novel Mode](http://specscripter.com/graphicNovelMode.png "Graphic Novel Mode")

<b>Screenplay Mode</b>

![Screenplay Mode](http://specscripter.com/screenplayMode.png "Screenplay Mode")

<b>System Requirements</b>

Linux Operationing System (Windows very soon.)

Python 2.7

Pygtk 3.14.15 + installed.

<b> Optional</b>

<p><a href="https://pypi.python.org/pypi/marisa-trie">marisa-trie</a> marisa-trie is needed for spell checking</p>

<p><a href="https://www.libreoffice.org/download/libreoffice-fresh/">LibreOffice</a> LibreOffice is needed to create pdf's</p>

<p><a href="http://quoteunquoteapps.com/courierprime/">Courier Prime Font</a> Courier Prime is needed for correct formatting in viewing and exporting.</p>

<h2>How To Use Diego</h2>
<i>At this time the app is in development and only meant for testing.</i>

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

<i>Optionally, pressing tab will reformat the line no matter where the cursor is placed on the line.</i>

<b>How To Auto-complete</b>

Diego uses The Double Cap Method. Hold down the Shift Key and press the character of the word you are looking for 2 times. Keep pressing the first letter of the word with the shift down to cycle through candidates. There are three things that auto-complete in Diego: Character Names and for screenplays Locations and Times.

<i>Characters in current scene are listed first. Character in rest of story follow in completion list.</i>

<b>Rename Story/Save As</b>

Double click the story title in the story view. Type in new name.

<b>Name/Rename A Scene Title</b>

Double click the scene title in the scene view. Type in new name.

<b>Find And Replace</b>

Control + r

<b>Save Story</b>

Control + s.  Also creates an rtf and pdf (if you have libreoffice installed).

<b>Save Story</b>

Control + Shift + s.  Also, just rename by double clicking the Story Title in Story View (but you will be working with the newly named document from that point on.)

<b>Open Story</b>

Control + o

<b>Prepend A New Scene/Page</b>

Select the Scene or page in which you want the Scene/Page to be inserted before.  Hold down Control and press enter.

<b>Increase/Decrease Font Size</b>

Place the cursor in the editor you want to resize font. Hold down Control and press + or - keys (plus or minus).

<b>Toggle Story/Scene Numbering</b>

Hold down Control and press #.

<b>Find In Story/Scene/Page</b>

Go to Story, Scene, or Page View. Type single word in Find Entry.

<b>Screenplay Mode</b>

Toggle the Screenplay Switch to Active. The first line of a scene now will auto-complete for Int/Ext, Location and Time.

<b>Set Author/Contact Information</b>

Press Atl + i, this information will be inserted into rtf and pdfs.

<i>Not implemented yet.</i>

<b>Move A Scene/Page</b>

Select the Scene or Page to be moved in the Scene/Page View.  Hold down Control key and press up or down arrow key.

<i>Not implemented yet.</i>

<b>Set Backup Disk</b>

Select Set Backup Disk from Right Click Menu. Follow prompt.

<i>Not implemented yet.</i>
