import sys

from gi.repository import Gtk, Gdk

if __name__ == "__main__":
    win = Gtk.Window()

    tv = Gtk.TextView()
    tv.props.left_margin = 10

    tv.get_buffer().create_tag("tag",
                                     background_rgba=Gdk.RGBA(0.0, 1.0, 0.0, 0.5),
                                     left_margin=20,
                                     right_margin=10,
                                     font="Sans " + str(12))

    tv.get_buffer().create_tag("tag2",
                                     background_rgba=Gdk.RGBA(0.0, 0.0, 1.0, 0.5),
                                     left_margin=40,
                                     right_margin=10,
                                     font="Sans " + str(12))

    insertTextOption = 1

    # Add No line or text.
    if insertTextOption == 0:
        pass

    text = 'one\n'
    #text += u"\u200B".encode('utf-8')

    insertIter = tv.get_buffer().get_iter_at_mark(tv.get_buffer().get_insert())
    tv.get_buffer().insert(insertIter, text, len(text))

    # insertIter = tv.get_buffer().get_iter_at_mark(tv.get_buffer().get_insert())
    # tv.get_buffer().insert(insertIter, u"\n\u200b".encode('utf-8'), 0)
    # tv.get_buffer().insert(insertIter, u"\n\u200b", 0)

    applyTagOption = 2

    startIter = tv.get_buffer().get_iter_at_line(0)
    endIter = tv.get_buffer().get_iter_at_line(1)
    endIter.backward_char()
    print ["first line text", tv.get_buffer().get_text(startIter, endIter, True)]
    tv.get_buffer().apply_tag_by_name('tag', startIter, endIter)

    startIter = tv.get_buffer().get_iter_at_line(1)
    endIter = tv.get_buffer().get_end_iter()
    # endIter.backward_char()
    print ["second line text", tv.get_buffer().get_text(startIter, endIter, True)]
    tv.get_buffer().apply_tag_by_name('tag2', startIter, endIter)


    charIter = tv.get_buffer().get_iter_at_line(0)
    print "printTags"
    print
    print

    tagNames = [name.props.name for name in charIter.get_tags()]
    print [charIter.get_char(), tagNames]

    character = charIter.forward_char()
    while character:
        tagNames = [name.props.name for name in charIter.get_tags()]
        print [charIter.get_char(), tagNames]
        character = charIter.forward_char()


    win.add(tv)
    win.show_all()
    Gtk.main()