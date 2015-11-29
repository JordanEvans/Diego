import sys

from gi.repository import Gtk, Gdk

if __name__ == "__main__":
    win = Gtk.Window()

    tv = Gtk.TextView()
    tv.props.left_margin = 20
    tv.get_buffer().create_tag("tag",
                                     background_rgba=Gdk.RGBA(0.0, 1.0, 0.0, 0.5),
                                     left_margin=20,
                                     right_margin=20,
                                     font="Sans " + str(12))

    insertTextOption = 1

    # Add No line or text.
    if insertTextOption == 0:
        pass

    # Just add a line, not text
    elif insertTextOption == 1:
        insertIter = tv.get_buffer().get_iter_at_mark(tv.get_buffer().get_insert())
        tv.get_buffer().insert(insertIter, "\n", len("\n"))

    # Just add text to existing first line.
    elif insertTextOption == 2:
        insertIter = tv.get_buffer().get_iter_at_mark(tv.get_buffer().get_insert())
        tv.get_buffer().insert(insertIter, "line", len("line"))

    # Put text on first line, and add another line with text.
    elif insertTextOption == 3:
        insertIter = tv.get_buffer().get_iter_at_mark(tv.get_buffer().get_insert())
        tv.get_buffer().insert(insertIter, "line\nline", len("line\nline"))

    insertIter = tv.get_buffer().get_iter_at_mark(tv.get_buffer().get_insert())
    # tv.get_buffer().insert(insertIter, u"\n\u200b".encode('utf-8'), 0)
    tv.get_buffer().insert(insertIter, u"\n\u200b", 0)

    applyTagOption = 2

    # Apply tag to the second line only.
    if applyTagOption == 1:
        startIter = tv.get_buffer().get_iter_at_line(1)
        endIter = tv.get_buffer().get_end_iter()
        tv.get_buffer().apply_tag_by_name('tag', startIter, endIter)

    # Apply tag to whole buffer.
    elif applyTagOption == 2:
        startIter = tv.get_buffer().get_start_iter()
        endIter = tv.get_buffer().get_end_iter()
        #endIter.backward_char()
        tv.get_buffer().apply_tag_by_name('tag', startIter, endIter)

    print [tv.get_buffer().get_text(startIter, endIter, True)]

    win.add(tv)
    win.show_all()
    Gtk.main()