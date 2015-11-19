from gi.repository import Gtk

def getText():

    dialog = Gtk.MessageDialog(
        None,
        Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
        Gtk.MessageType.QUESTION,
        Gtk.ButtonsType.OK,
        None)
    dialog.set_markup('Please enter your <b>name</b>:')
    entry = Gtk.Entry()

    hbox = Gtk.HBox()
    hbox.pack_start(Gtk.Label("Name:"), 0, 5, 5)
    hbox.pack_end(entry, 0, 0, 0)

    dialog.format_secondary_markup("This will be used for <i>identification</i> purposes")

    dialog.vbox.pack_end(hbox, 1, 1, 0)
    dialog.show_all()

    dialog.run()
    text = entry.get_text()
    dialog.destroy()
    return text