# Diego

<h3>Simple. Fast. Organized.</h3>

Diego's goal is to be The Simplest and the Fastest Scriptwriting software for Graphic Novel writers. Diego also seconds as specscript software.

Diego has traded feature bloat for simplicity. Only features that are neccessary to get the job done are added. Diego's design centers around keeping the writers hands on the keyboard. Keyboard shortcuts replace the common interface cluttered with buttons and menus and submenus.

Each Story, Scene and Page has an Info/Abstract Text area that allows the writer to outline their story by creating abstracts. This text area works as a  convenient place to store premises for new story ideas that may turn into a full script at some point.

When Diego saves, three documents are created: the Diego document, an RTF for extra tweeking, and a PDF.

<img src="http://specscripter.com/screenshot.png">

<b>System Requirements</b>

Linux Operationing System

Pygtk 3.14.15 installed.

<p><a href="http://quoteunquoteapps.com/courierprime/">Courier Prime Font</a> Needs to be installed for correct format in viewing and exporting.</p>

Here's some instructions for usage:

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

If the line is empty, just press the Spacebar. If the line has text, then place the cursor at the beginning of the line and hit Spacebar.

<i>Optionally, pressing tab will reformat the line no matter where the cursor is placed on the line.</i>

<b>How to Auto Complete Names</b>

Hold down shift. Type the first letter of the characters name. Press same character to cycle through potential names.

<i>Characters in current scene are listed first. Character in rest of story follow in completion list.</i>

<b>Rename Story/Save As</b>

Double click the story title in the story view. Type in new name.

<b>Name/Rename A Scene Title</b>

Double click the scene title in the scene view. Type in new name.

<b>Find And Replace</b>

Control + r

<b>Toggle Script View or Abstract View</b>

Hit Escape key while in the respective editor.

<b>Add Abstract to Story, Scenes and Pages</b>

Go to the Story, Scene or Page you want to write the abstract and type it in the Abstract editor above the Script editor.

<b>Save Story</b>

Control + s.  Also creates an rtf and pdf (if you have libreoffice installed).

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

<i>Not implemented. Hit enter to navigate through selections.</i>

<b>Screenplay Mode</b>

Toggle the Screenplay Switch to Active. The first line of a scene now will autocomplete for Int/Ext, Location and Time.

<b>Autocomplete Int/Ext, Location and Time</b>

Activate Screenplay Mode. On first line of a scene, hold down Shift Key and press the letter twice that starts with word you want to autocomplete.