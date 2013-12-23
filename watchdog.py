"""
Ensures that we don't have rogue WinSCP sessions laying around. Checks ever 2 seconds to see if Sublime is running;
if it's not, it closes all existing WinSCP sessions that we opened through Sublime, and then kills itself.

"""

import sys
import subprocess
import threading

def pid_running(pid):
    out = subprocess.check_output(["tasklist","/fi","PID eq {}".format(pid)]).strip()
    if out == "INFO: No tasks are running which match the specified criteria.":
    	return False
    return True

def kill_all_procs(pids):
	for pid in pids:
		if pid_running(pid):
			subprocess.Popen('TASKKILL /F /PID {pid} /T'.format(pid=pid), shell=True)

def parent_running(parent, pids):
	if pid_running(parent) is False:
		kill_all_procs(pids)
		sys.exit()
	else:
		threading.Timer(2, parent_running, [parent_id, running_pids]).start()



if __name__ == '__main__':
	parent_id = sys.argv[1]
	pids = sys.argv[2:]
	running_pids = [x for x in pids if pid_running(x)]

	parent_running(parent_id, pids)	