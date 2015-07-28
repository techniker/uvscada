from uvscada.planner import Planner
from uvscada.benchmark import Benchmark

import Queue
import threading
from PyQt4.QtCore import *
import time
import os
import json

def dbg(*args):
    if len(args) == 0:
        print
    elif len(args) == 1:
        print 'threading: %s' % (args[0], )
    else:
        print 'threading: ' + (args[0] % args[1:])

'''
Try to seperate imaging and movement
For now keep unified in planner thread
'''
class ImagingThread(QThread):
    def __init__(self):
        self.queue = Queue.Queue()
        self.running = threading.Event()
    
    def run(self):
        self.running.set()
        while self.running.is_set():
            time.sleep(1)
    
    def stop(self):
        self.running.clear()

'''
Offloads controller processing to another thread (or potentially even process)
Makes it easier to keep RT deadlines and such
However, it doesn't provide feedback completion so use with care
(other blocks until done)
TODO: should block?
'''

class CncThread(QThread):
    def __init__(self, hal, cmd_done):
        QThread.__init__(self)
        self.queue = Queue.Queue()
        self.hal = hal
        self.running = threading.Event()
        self.idle = threading.Event()
        self.idle.set()
        self.normal_running = threading.Event()
        self.normal_running.set()
        self.cmd_done = cmd_done
        
    def setRunning(self, running):
        if running:
            self.normal_running.set()
        else:
            self.normal_running.clear()
    def wait_idle(self):
        while True:
            time.sleep(0.15)
            if self.idle():
                break
        
    def cmd(self, cmd, *args):
        self.queue.put((cmd, args))

    def run(self):
        self.running.set()
        self.idle.clear()
        self.hal.on()
        
        while self.running.is_set():
            if not self.normal_running.isSet():
                self.normal_running.wait(0.1)
                continue
            try:
                (cmd, args) = self.queue.get(True, 0.1)
                self.idle.clear()
            except Queue.Empty:
                self.idle.set()
                continue
            
            def default(*args):
                raise Exception("Bad command %s" % (cmd,))
            
            def mv_abs(pos):
                self.hal.mv_abs(pos)
                return self.hal.pos()

            def mv_rel(pos):
                self.hal.mv_rel(pos)
                return self.hal.pos()
            
            def home(axes):
                self.hal.home(axes)
                return self.hal.pos()
            
            ret = {
                'mv_abs':   mv_abs,
                'mv_rel':   mv_rel,
                'stop':     self.hal.stop,
                'estop':    self.hal.estop,
                'unestop':  self.hal.unestop,
                'home':     home,
            }.get(cmd, default)(*args)
            self.cmd_done(cmd, args, ret)
    
    def stop(self):
        self.running.clear()        

# Sends events to the imaging and movement threads
class PlannerThread(QThread):
    plannerDone = pyqtSignal()

    def __init__(self,parent, rconfig):
        QThread.__init__(self, parent)
        self.rconfig = rconfig
        self.planner = None
        
    def log(self, msg):
        #print 'emitting log %s' % msg
        #self.log_buff += str(msg) + '\n'
        self.emit(SIGNAL('log'), msg)
    
    def setRunning(self, running):
        planner = self.planner
        if planner:
            planner.setRunning(running)
        
    def run(self):
        try:
            self.log('Initializing planner!')
    
            scan_config = json.load(open('scan.json'))
            
            rconfig = self.rconfig
            obj = rconfig['uscope']['objective'][rconfig['obj']]
            im_w_pix = int(rconfig['imager']['width'])
            im_h_pix = int(rconfig['imager']['height'])
            x_um = float(obj['x_view'])
            self.planner = Planner(scan_config=scan_config, hal=rconfig['cnc_hal'], (im_w_pix, im_h_pix), x_um / im_w_pix, rconfig['out_dir'],
                    progress_cb=rconfig['progress_cb'],
                    overwrite=rconfig['overwrite'], dry=rconfig['dry'],
                    img_scalar=float(rconfig['uscope']['imager']['scalar']),
                    log=self.log, verbosity=2)
            self.log('Running planner')
            b = Benchmark()
            self.planner.run()
            b.stop()
            self.log('Planner done!  Took : %s' % str(b))
        except Exception as e:
            self.log('WARNING: planner thread crashed: %s' % str(e))
            raise
        finally:
            self.plannerDone.emit()
