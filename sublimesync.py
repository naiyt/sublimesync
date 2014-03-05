import sublime
import sublime_plugin
import subprocess
import sys
import json
import threading
import os
import uuid

package_name = 'sublimesync'

class Sync(threading.Thread):
    """A thread is created for each syncing process"""
    def __init__(self, txt_path, sync_from, sync_to, hostname):
        self.txt_path = txt_path
        self.sync_from = sync_from
        self.sync_to = sync_to
        self.hostname = hostname
        self.path = self.create_sync_txt()
        self.running = True
        threading.Thread.__init__(self)
        

    def create_sync_txt(self):
        """Generates a unique sync text file with the details of what to sync for WinSCP"""
        file_path = os.path.join(self.txt_path, '{0}-{1}-sync.txt'.format(self.hostname, uuid.uuid4()))
        f = open(file_path, 'w')
        sync_str = "open {0}\nkeepuptodate -delete \"{1}\" {2}".format(self.hostname, self.sync_from, self.sync_to)
        f.write(sync_str)
        f.close()
        return file_path

    def run(self):
        print "Now connecting using WinSCP..."
        self.execute('winscp.com /defaults /script="{0}"'.format(self.path))

    def execute(self, command):
        """Thanks to: http://stackoverflow.com/a/4418193/1026980"""
        self.process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    
        while True:
            """Write the output to stdout in a non-blocking manner"""
            nextline = self.process.stdout.readline()
            if nextline == '' and self.process.poll != None:
                break
            sys.stdout.write(nextline)
            sys.stdout.flush()
            
    def stop(self):
        """
        Kills the existing connection. This is kind of a nasty hack at the moment, but I was running into issues
        with properly closing threads and subprocesses on Windows

        """

        if self.running:
            print 'Killing connection {0}'.format(self.process.pid)
            self.running = False
            subprocess.Popen('TASKKILL /F /PID {pid} /T'.format(pid=self.process.pid), shell=True)
            print 'Removing sync file {0}...'.format(self.path)
            os.remove(self.path)
            
    

class SublimeSyncCommand(sublime_plugin.TextCommand):

    def run(self, edit, setup_sync=None, start_sync=None, stop_sync=None):

        if setup_sync is not None:
            self.setup_sync()

        if start_sync is not None:
            self.start_sync()

        if stop_sync is not None:
            self.stop_sync()

    def setup_sync(self):
        """
        Opens up the JSON file with the folders to keep synced. It automatically adds any folders currently
        open in Sublime to this list; you just have to put in the hostname and the remote directory to keep up to
        date, and set 'keep_synced' to True or False

        """

        print os.getpid()

        folders = sublime.active_window().folders() # All active folders
        path = os.path.join(sublime.packages_path(), package_name, 'to_sync.json')
        f = open(path, 'r')

        try:
            json_obj = json.loads(f.read())
        except ValueError:
            json_obj = json.loads('{}') # Initialize w/blank dictionary

        f.close()
        f = open(path, 'w')

        # Add open folders to the file if they are not there
        for folder in folders:
            if folder not in json_obj:
                json_obj[folder] = {'sync_to': '', 'hostname': '', 'keep_synced': False}

        json.dump(json_obj, f, indent=4)
        f.close()

        sublime.active_window().open_file(path) # Open the file for editing

    def start_sync(self):
        """Open the JSON settings file and initiate syncs for any that have keep_synced set to True"""
        self.stop_sync() # Stop any existing threads FIRST. We don't want multiple processes syncing the same files.

        if hasattr(sublime, 'threads') == False:
            sublime.threads = []

        sublime.status_message('Starting Sync...')
        path = os.path.join(sublime.packages_path(), package_name, 'to_sync.json')
        f = open(path, 'r')
        json_obj = json.loads(f.read())

        txt_path = os.path.join(sublime.packages_path(), package_name, 'synctxts')

        for folder in json_obj:
            sync_from = folder
            info = json_obj[folder]
            if info['keep_synced']:
                sync_to = info['sync_to']
                hostname = info['hostname']
                sublime.status_message('Initiating a sync with {0}'.format(hostname))
                self.init_sync(txt_path, sync_from, sync_to, hostname)

        self.watchdog = Watchdog()
        self.watchdog.start()

    
    def init_sync(self, txt_path, sync_from, sync_to, hostname):
        """Create a thread that syncs the specified folder"""
        thread = Sync(txt_path, sync_from, sync_to, hostname)
        thread.start()
        # Keeping track of our thread so that we can persistently access them through the Sublime session
        if hasattr(sublime, 'threads'):
            sublime.threads.append(thread)
        else:
            sublime.threads = [thread]

    def stop_sync(self):
        print 'Stopping all existing syncing threads'
        sublime.status_message('Stopping all existing syncing threads')
        if hasattr(sublime, 'threads'):
            for thread in sublime.threads:
                thread.stop()

        # Ensure we don't have any stale sublime syncing text files (if the user quit before cancelling the sync)
        path = os.path.join(sublime.packages_path(), package_name, 'synctxts')
        for curr_file in os.listdir(path):
            file_path = os.path.join(path, curr_file)
            os.remove(file_path)

        if hasattr(self, 'watchdog'):
            self.watchdog.stop()



class Watchdog(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        running_threads = [x for x in sublime.threads if x.running]
        full_threads = []
        thread_count = 0
        while thread_count < len(running_threads):
            for thread in running_threads:
                if hasattr(thread, 'process'):
                    if thread not in full_threads:
                        thread_count += 1
                        full_threads.append(thread)
            running_threads = [x for x in sublime.threads if x.running]

        watchdog_path = os.path.join(sublime.packages_path(), package_name, 'watchdog.py')
        args = [str(x.process.pid) for x in full_threads]

        command = 'python "{0}"'.format(watchdog_path)
        command += ' {0}'.format(os.getpid())
        for arg in args:
            command += ' {0}'.format(arg)

        self.watchdog = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)



    def stop(self):
        subprocess.Popen('TASKKILL /F /PID {pid} /T'.format(pid=self.watchdog.pid), shell=True)
