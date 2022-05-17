from ast import If
import sys, types, os
import tkinter
from time import localtime
from datetime import timedelta,datetime
from math import sin, cos, pi
from threading import Thread
from typing_extensions import Self
from astral import *
from astral.sun import sun
import pytz
import json


try:
    from tkinter import *       # python 3
except ImportError:
    try:
       from mtTkinter import *  # for thread safe
    except ImportError:
       from Tkinter import *    # python 2

hasPIL = True
# we need PIL for resizing the background image
# in Fedora do: yum install python-pillow-tk
# or yum install python3-pillow-tk
try:
    from PIL import Image, ImageTk
except ImportError:
    hasPIL = False

class mapper:
    """ Class for handling the mapping from window coordinates
  to viewport coordinates."""

    def __init__(self, world, viewport):
        """ Constructor.

        @param world window rectangle.
        @param viewport screen rectangle."""

        self.world = world
        self.viewport = viewport
        x_min, y_min, x_max, y_max = self.world
        X_min, Y_min, X_max, Y_max = self.viewport
        f_x = float(X_max-X_min) / float(x_max-x_min)
        f_y = float(Y_max-Y_min) / float(y_max-y_min)
        self.f = min(f_x,f_y)
        x_c = 0.5 * (x_min + x_max)
        y_c = 0.5 * (y_min + y_max)
        X_c = 0.5 * (X_min + X_max)
        Y_c = 0.5 * (Y_min + Y_max)
        self.c_1 = X_c - self.f * x_c
        self.c_2 = Y_c - self.f * y_c

    def __windowToViewport(self, x, y):
        """Maps a single point from world coordinates to viewport (screen) coordinates.

        @param x, y given point.
        @return a new point in screen coordinates."""

        X = self.f *  x + self.c_1
        Y = self.f * -y + self.c_2      # Y axis is upside down
        return X , Y

    def windowToViewport(self,x1,y1,x2,y2):
        """ Maps two points from world coordinates to viewport (screen) coordinates.

        @param x1, y1 first point.
        @param x2, y2 second point.
        @return two new points in screen coordinates."""

        return self.__windowToViewport(x1,y1),self.__windowToViewport(x2,y2)

class makeThread (Thread):

    """ Class for creating a new thread. """

    def __init__ (self,func):
        """Creates a thread.

        Constructor.

        @param func function to run on this thread."""

        Thread.__init__(self)
        self.__action = func
        self.debug = False

    def __del__ (self):
        """Destructor """

        if ( self.debug ): print ("Thread end")


    def run (self):
        """ Starts this thread."""
        
        if ( self.debug ): print ("Thread begin")
        self.__action()


class clock:
    """Class for drawing a simple analog clock.
    The image path is hardcoded, you can pick whatever you like. 
    Currently we're just using a background color"""

    def __init__(self,root,deltahours = 0,sImage = True,w = 400,h = 400,useThread = False):
        """Constructor.

        @param deltahours time zone.
        @param sImage whether to use a background image.
        @param w canvas width.
        @param h canvas height.
        @param useThread whether to use a separate thread for running the clock."""
        self.index = 0
        self.createdictionary()

        self.world       = [-1,-1,1,1]
        self.imgPath     = ''  # image path
        if hasPIL and os.path.exists (self.imgPath):
           self.showImage = sImage
        else:
           self.showImage = False

        self.setColors()
        self.circlesize  = 0.09
        self._ALL        = 'handles'
        self.root        = root
        width, height    = w, h
        self.pad         = width/16

        if self.showImage:
           self.fluImg = Image.open(self.imgPath)

        self.root.bind("<Escape>", lambda _ : root.destroy())
        self.delta = timedelta(hours = deltahours)
        self.canvas = Canvas(root, width = width, height = height, background = self.bgcolor)
        viewport = (self.pad,self.pad,width-self.pad,height-self.pad)
        self.T = mapper(self.world,viewport)
        self.root.title('Clock')
        self.canvas.bind("<Configure>",self.resize)
        self.root.bind("<KeyPress-i>", self.toggleImage)
        self.drawbutton()
        self.canvas.pack(fill=BOTH, expand=YES)
        self.showtimestamp()

        if useThread:
           st=makeThread(self.poll)
           st.debug = True
           st.start()
        else:
           self.poll()

    def resize(self,event):
        """Called when the window changes, by means of a user input."""

        sc = self.canvas
        sc.delete(ALL)            # erase the whole canvas
        width  = sc.winfo_width()
        height = sc.winfo_height()

        imgSize = min(width, height)
        self.pad = imgSize/16
        viewport = (self.pad,self.pad,width-self.pad,height-self.pad)
        self.T = mapper(self.world,viewport)

        if self.showImage:
           flu = self.fluImg.resize((int(0.8*0.8*imgSize), int(0.8*imgSize)), Image.ANTIALIAS)
           self.flu = ImageTk.PhotoImage(flu)
           sc.create_image(width/2,height/2,image=self.flu)
        else:
           self.canvas.create_rectangle([[0,0],[width,height]], fill = self.bgcolor)

        self.redraw()             # redraw the clock


    def setColors(self):
        """Sets the clock colors."""

        if self.showImage:
           self.bgcolor     = 'antique white'
           self.timecolor   = 'dark orange'
           self.circlecolor = 'dark green'
           self.reddefault  = '#b80000'
        else:
           self.bgcolor     = '#000000'
           self.timecolor   = '#ffffff'
           self.circlecolor = '#808080'
           self.reddefault  = '#b80000'

    

    def toggleImage(self,event):
        """Toggles the displaying of a background image."""

        if hasPIL and os.path.exists (self.imgPath):
           self.showImage = not self.showImage
           self.setColors()
           self.resize(event)

    def redraw(self):
        """Redraws the whole clock."""

        start = pi/2              # 12h is at pi/2
        step = pi/6
        for i in range(12):       # draw the minute ticks as circles
            angle =  start-i*step
            x, y = cos(angle),sin(angle)
            self.paintcircle(x,y)

        start = pi/2
        step = pi/12
        hr, hs = self.daylight()
        for i in range(24):       # draw the hour ticks as circles
            if i <= hs and i >= hr: #change circle color if time is between sunset and sunrise
                self.reddefault = "dark orange"
            else:
                self.reddefault = "#b80000"
            angle =  start-i*step
            x, y = cos(angle),sin(angle)
            self.paintcirclehour(x,y)
        self.paintredhandle()
        self.painthms()           # draw the handles
        if not self.showImage:
           self.paintcircle(0,0)  # draw a circle at the centre of the clock

    def paintredhandle(self):
        """
        Paint red handle that moves according to timezone.
        """
        self.canvas.delete(self._ALL)
        # d = datetime.now()
        timezone = pytz.timezone(f"{self.data['cities'][self.index]['region']}/{self.data['cities'][self.index]['city']}")
        d_aware = datetime.now(timezone)
        T = datetime.timetuple(d_aware-self.delta)
        x,x,x,h,m,s,x,x,x = T
        scl = self.canvas.create_line
        angle = pi/2 - pi/12 * (h + m/60.0)
        x, y = cos(angle)*0.60,sin(angle)*0.60
        # draw the red handle
        scl(self.T.windowToViewport(0,0,x,y), fill = self.reddefault, tag=self._ALL, width = self.pad/4)

    """Draws the handles."""

    def painthms(self):
        T = datetime.timetuple(datetime.utcnow()-self.delta)
        x,x,x,h,m,s,x,x,x = T
        self.root.title('%02i:%02i:%02i' %(h,m,s))
        scl = self.canvas.create_line
        angle = pi/2 - pi/6 * (h + m/60.0)
        x, y = cos(angle)*0.70,sin(angle)*0.70
        # draw the hour handle
        scl(self.T.windowToViewport(0,0,x,y), fill = self.timecolor, tag=self._ALL, width = self.pad/3)
        angle = pi/2 - pi/30 * (m + s/60.0)
        x, y = cos(angle)*0.90,sin(angle)*0.90
        # draw the minute handle
        scl(self.T.windowToViewport(0,0,x,y), fill = self.timecolor, tag=self._ALL, width = self.pad/5)
        angle = pi/2 - pi/30 * s
        x, y = cos(angle)*0.95,sin(angle)*0.95
        # draw the second handle
        scl(self.T.windowToViewport(0,0,x,y), fill = self.timecolor, tag=self._ALL, arrow = 'last')



    def paintcircle(self,x,y):
        """Draws a circle at a given point.

        @param x,y given point."""

        ss = self.circlesize / 2.0
        sco = self.canvas.create_oval
        sco(self.T.windowToViewport(-ss+x,-ss+y,ss+x,ss+y), fill = self.circlecolor)

    def paintcirclehour(self,x,y):
        """Draws a small circle at a given point.

        @param x,y given point."""

        ss = self.circlesize / 5.0
        sco = self.canvas.create_oval
        sco(self.T.windowToViewport(-ss+x,-ss+y,ss+x,ss+y), fill = self.reddefault)

    def createdictionary(self):
        """
        Create dictionary with localtime.json.
        """
        with open('localtime.json', encoding='utf-8') as localtime:
            self.data = json.load(localtime)

    def changetimestamp(self):
        """
        Change timestamp according to localtime.json.
        """
        if self.index < 19:
            self.index = self.index + 1
        else:
            self.index = 0
        self.lbl.destroy()
        self.showtimestamp()

    def showtimestamp(self):
        """
        Show label with timezone info.
        """
        self.lbl = Label(self.root, text=f"{self.data['cities'][self.index]['city']}/{self.data['cities'][self.index]['region']} - UTC {self.data['cities'][self.index]['offset']}", font=('Helvetica 12 bold'))
        self.lbl.pack()

    def drawbutton(self):
        """
        Draws the button at the top side of the canvas.
        """
        tkinter.Button(self.root, text="Change UTC", command=self.changetimestamp).pack()

    """Animates the clock, by redrawing everything after a certain time interval."""

    def poll(self):
        """Animates the clock, by redrawing everything after a certain time interval."""

        self.redraw()
        self.root.after(200,self.poll)

    
    def daylight(self):
        """Get sunrise and sunset time from main location"""

        today = datetime.date (datetime.now ())
        city = LocationInfo(self.data['cities'][self.index]['city'], self.data['cities'][self.index]['region'], f"{self.data['cities'][self.index]['region']}/{self.data['cities'][self.index]['city']}", self.data['cities'][self.index]['coordinates']['latitude'], self.data['cities'][self.index]['coordinates']['longitude'])
        sun_data = sun(city.observer, today,
        tzinfo = pytz.timezone('America/Manaus'))
        hr , mr , _ = datetime.timetuple(sun_data['sunrise'])[3:6]
        hs , ms , _ = datetime.timetuple(sun_data['sunset'])[3:6]
        return hr, hs
        
def main(argv=None):
    """Main program for testing.

        @param argv time zone, image background flag,
        clock width, clock height, create thread flag."""

    if argv is None:
       argv = sys.argv
    if len(argv) > 2:
       try:
           deltahours = int(argv[1])
           sImage = (argv[2] == 'True')
           w = int(argv[3])
           h = int(argv[4])
           t = (argv[5] == 'True')
       except ValueError:
           print ("A timezone is expected.")
           return 1
    else:
       deltahours = 3
       sImage = True
       w = h = 400
       t = False

    root = Tk()
    root.geometry ('+0+0')
    # deltahours: how far are you from utc?
    # Sometimes the clock may be run from another timezone ..
    clock(root,deltahours,sImage,w,h,t)

    root.mainloop()

if __name__=='__main__':
    sys.exit(main())
