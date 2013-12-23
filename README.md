sublimesync
===========

Uses WinSCP to keep a remote directory synced in Sublime

In the past, I've run into some annoying issues with developing in Sublime over a remote connection. (For example, I like to program in Sublime on my desktop, but I prefer to write the code on my laptop, running Ubuntu.) You can just edit the file remotely with something like WinSCP, but the problem is you can't have the folder open in Sublime, which means you don't get the benfits of Ctrl-P, and stuff like that. There are some solutions out there, but I wasn't able to find one that both worked well and didn't cost anything.

WinSCP comes with a feature that allows you to sync a local and a remote repository. You can also do this headless over the command line. So in an effort to make modifying remote files easier, I wrote this Sublime plugin to handle it for you. You should have a local copy of whatever you're editing, and it will sync it with a remote version automagically.

This thing is **very early** in development and I don't know if I can recommend using it at this point. If you do, just remember I can't speak for the stability or security of it currently. Use it at your own risk.

Installation
------------

Just throw this whole thing in your Packages directory in Sublime. It currently only works on Windows (but can sync to any remote OS without a problem). So in my case, I use it to sync Windows -> Ubuntu.

Usage
-----

Keybindings are in `Default (Windows).sublime-keymap`, and can be edited there.

**ctrl+7** - Set the directories you want to sync. Opens up the `to_sync.json` file, which is how the plugin determines what you want synced. By default, it will automatically add all of the directories you currently have open in Sublime, but you can add more as needed.

* `sync_to` - defines the path on the remote machine.
* `hostname` - should be a hostname that WinSCP already recognizes. You'll want to make sure it's a saved session in WinSCP with that name. Preferably with a key based login. The plugin doesn't support password prompting.
* `keep_synced` - whether to sync these directories.

**ctrl+8** - Starts syncing the directories where `keep_synced` is set to true in `to_sync.json`.

**ctrl+9** - Stops all syncing.


When a sync is started, a watchdog process is spawned to make sure the WinSCP sessions are closed if you close Sublime without hitting `ctrl+9` first. Sublime unfortunately does not appear to have any sort of callback on closing, so something like this was necessary. The implementation is admittedly naive and could be improved. But for now it works to make sure you don't have all sorts of rogue WinSCP sessions laying around whenever you close Sublime.