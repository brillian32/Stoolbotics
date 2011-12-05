#!/usr/bin/env python
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

import sys, os, json, Image, numpy, math
import config

import objects
import tools.display as display

class mouse():
    def __init__(self):
        self.x = None
        self.y = None
        
        self.up = False
        self.down = False
        self.oldMouseDraggedX = None
        self.oldMouseDraggedY = None
        self.middlePressed = False
        self.rightPressed = False
        self.leftPressed = False
        
class simulator():
    def __init__(self, robot, room):
        self.robot = robot
        self.room = room
        self.mouse = mouse()

        self.width = 1000
        self.height = 600

        self.angleY = -135
        self.angleX = 245

        self.transX = 30.0
        self.transY = -30.0
        self.transZ = 25.0

        self.tscale = .2
        self.scale = 10
        self.room.scale = self.scale
        self.zoom = 1.6

        self.robot.forwardkin()
        self.robot.timestep()
        self.robot.print_vars()
        
        self.text = ['Interact by typing commands or using the mouse!', 'Welcome to stoolbotics!']
        self.text += " "
        
        self.cmd = ''
        self.cmd_selection = -1
        
    def timestep(self):
        self.robot.forwardkin()
        self.robot.timestep(self.tscale)
        glutPostRedisplay()
    
    def _updateMouse(self, x, y):
        self.mouse.oldMouseDraggedX = self.mouse.x
        self.mouse.oldMouseDraggedY = self.mouse.y
        self.mouse.x = x
        self.mouse.y = y

    # Mouse motion callback routine.
    def mouseMotion(self, x, y):
        self._updateMouse(x, y)

    def mouseDragged(self, x, y):
        self._updateMouse(x, y)
        
        v1 = math.sin(self.angleX * config.pi / 180 )
        v2 = math.cos(self.angleY * config.pi / 180 )
        changeX = v1*(x - self.mouse.oldMouseDraggedX)
        changeY = v2*(y - self.mouse.oldMouseDraggedY)

        # why are these mixed up? it breaks without it
        self.angleX += changeY
        self.angleY -= changeX
        
        self.screenprint("Angle = (" + str(round(self.angleX, 2)) + ", " + str(round(self.angleY, 2)) + ")")
        if (self.angleX < 180):
            self.angleX = 180
        if (self.angleX > 360):
            self.angleX = 360
        glutPostRedisplay()

    #The mouse callback routine.
    def mouseControl(self, button, state, x, y):
        self._updateMouse(x, y)
        print 'X = ' + str(x) +' Y = ' + str(y)
        if (button == 3):# Zoom in
            self.camera_zoom('in')
            return
        elif (button == 4): # Zoom out
            self.camera_zoom('out')
            return
        
        # clear mouse object
        self.mouse.leftPressed = False
        self.mouse.middlePressed = False
        self.mouse.rightPressed = False
        self.up = False
        self.down = False
        
        m = self.mouse
        s  = ''
        if state == GLUT_DOWN:
            m.down = True
            s = 'down'
        else:
            m.up = True
            s = 'up'
        if button == GLUT_LEFT_BUTTON:
            m.leftPressed = True
            print "LEFT " + s
        if button == GLUT_MIDDLE_BUTTON:
            m.middlePressed = True
            print "MIDDLE " + s
        if button == GLUT_RIGHT_BUTTON:
            m.rightPressed = True
            print "RIGHT " + s

        if (m.middlePressed or m.rightPressed) and m.down:
            m.oldMouseDraggedX = x
            m.oldMouseDraggedY = y

    def camera_zoom(self, what = 'in'):
        if what == 'in':
            if (self.zoom > 0.1):
                self.zoom -= 0.1
        elif what == 'out':
            self.zoom += 0.1
        print "Zoom = " + str(self.zoom)
        self.resize(self.width, self.height)
        glutPostRedisplay()

    def keyboard_special(self, key, x, y):
        self._updateMouse(x, y)
        amount = 5
        if key == GLUT_KEY_RIGHT:
            self.transX += amount
        elif key == GLUT_KEY_LEFT:
            self.transX -= amount
        elif key == GLUT_KEY_DOWN:
            if not self.cmd_selection == -1:
                self.cmd_selection += 1
            if self.cmd_selection == -1:
                self.cmd = self.text[-1] = ""
            self.transY -= amount
        elif key == GLUT_KEY_UP:
            if not -self.cmd_selection == len(self.text):
                self.cmd_selection -= 1
            self.transY += amount
        self.cmd = self.text[-1] = self.text[self.cmd_selection]
        glutPostRedisplay()

    def handle_cmd(self, cmd):
        pass

    def keyboard(self, key, x, y):
        self._updateMouse(x, y)
        
        esc = chr(27)
        backspace = chr(8)
        carriagereturn = chr(13)
        newline = chr(10)

        
        if key in [carriagereturn, newline]:
            self.text.append(" ")
            self.handle_cmd(self.cmd)
            self.cmd = ''
            print "enter pressed"
        elif key == backspace:
            self.cmd = self.cmd[:-1]
        elif key == esc:
            sys.exit(0)
        else:
            self.cmd += key
        self.text[-1] = self.cmd
        
        glutPostRedisplay()
        return
        if key == 'p':
            glutIdleFunc(self.timestep)
        elif key == 's':
            glutIdleFunc(None)
        elif key == '+':
            self.camera_zoom('in')
        elif key == '-':
            self.camera_zoom('out')
        elif key == 'f':
            self.tscale += .01
        elif key == 'd':
            self.tscale -= .01
        elif key == 'y':
            s = glReadPixels(0, 0, self.width, self.height, GL_RGB, GL_UNSIGNED_BYTE)
            img = Image.new('RGB', (self.width, self.height))
            img.fromstring(s)
            img2 = img.transpose(Image.FLIP_TOP_BOTTOM)
            img2.save("screendump.png")
        
        
    def screenprint(self, text):
        self.text.append(text)
    
    def draw(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        glPushMatrix()
        #looking at x/y plane - down z axis
        glTranslatef(self.transX, self.transY, self.transZ)
        
        glRotatef(self.angleY, 0.0, 1.0, 0.0)
        glRotatef(self.angleX, 1.0, 0.0, 0.0)
        
        self.room.render()
        
        glColor3f(0, 0, 0)
        #display.draw_axes(20, '1')
        
        self.robot.render()
        glPopMatrix()

        # reference axis
        glPushMatrix()
        glTranslatef(self.zoom*40.0, self.zoom*-55.0, 400.0)

        glRotatef(self.angleY, 0.0, 1.0, 0.0)
        glRotatef(self.angleX, 1.0, 0.0, 0.0)
        display.draw_axes(self.zoom*13, '')
        
        glPopMatrix()

        glPushMatrix()
        glTranslatef(-self.zoom*.094*self.width, -self.zoom*.094*self.height, 400.0)
        
        glColor4f(0.5, 0.5, 1.0, 0.4)
        
        x0 = y0 = self.zoom*-3 # bottom left corner
        x1 = self.zoom*70 # width
        y1 = self.zoom*110 # height
        
        glBegin(GL_QUADS)
        glVertex3f(x0, y0, -1)
        glVertex3f(x1, y0, -1)
        glVertex3f(x1, y1, -1)
        glVertex3f(x0, y1, -1)
        glEnd()
        
        glColor4f(0.0, 0.0, 0.0, 1.0)
        
        self.text = self.text[-36:]
        
        prompt = ">> "
        for i in range(len(self.text)):
            if self.text[i][:len(prompt)] != prompt:
                self.text[i] = prompt + self.text[i]
        
        i = 0
        max_line_chr = 38
        for text in reversed(self.text):
            if len(text) <= max_line_chr:
                glPushMatrix()
                display.text_at_pos(0, self.zoom*i*3, 0, text, font=GLUT_BITMAP_9_BY_15)
                glPopMatrix()
                i += 1
            else:
                tmp = []
                for j in range(0, len(text), max_line_chr):
                    segment = text[j:j + max_line_chr]
                    n = max_line_chr - len(segment)
                    for _ in range(n):
                        segment += ' '
                    tmp.append(segment)
                tmp.reverse()
                for c in tmp:
                    glPushMatrix()
                    display.text_at_pos(0, self.zoom*i*3, 0, c, font=GLUT_BITMAP_9_BY_15)
                    glPopMatrix()
                    i += 1
        glPopMatrix()
        
        glutSwapBuffers()

    def resize(self, w, h):
        self.width = w
        self.height = h
        glViewport(0, 0, w, h)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        new_w = self.zoom*w/self.scale
        new_h = self.zoom*h/self.scale

        glOrtho (-new_w, new_w, -new_h, new_h, -500.0, 500.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

def setup():
    if config.enable_lighting:
        ambient = [1.0, 1.0, 1.0, 1.0]
        #diffuse = [1.0, 1.0, 1.0, 1.0]
        #specular = [1.0, 1.0, 1.0, 1.0]
        #position = [0.0, 0.0, -200.0, 0.0]

        lmodel_ambient = [0.2, 0.2, 0.2, 1.0]
        local_view = [0.0]

        glLightfv(GL_LIGHT0, GL_AMBIENT, ambient)
        #glLightfv(GL_LIGHT0, GL_DIFFUSE, diffuse)
        #glLightfv(GL_LIGHT0, GL_POSITION, position)
        glLightModelfv(GL_LIGHT_MODEL_AMBIENT, lmodel_ambient)
        glLightModelfv(GL_LIGHT_MODEL_LOCAL_VIEWER, local_view)

        #glFrontFace(GL_CW)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        #glEnable(GL_AUTO_NORMAL)
        #glEnable(GL_NORMALIZE)

    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glEnable(GL_DEPTH_TEST)
    glClearColor(1.0, 1.0, 1.0, 0.0)

    # Enable two vertex arrays: position and normal.
    glEnableClientState(GL_VERTEX_ARRAY)
    glEnableClientState(GL_NORMAL_ARRAY)

def create_robot(filename):
    r = json.loads(open(filename).read(), object_hook=lambda d: objects.robot(d))
    return r

def main():
    room = objects.room(200, 200, 200, False)
    robot = create_robot('robots/' + config.robot_file)
    s = simulator(robot, room)

    glutInit()
    glutInitDisplayMode(GLUT_RGB | GLUT_DOUBLE | GLUT_DEPTH)
    glutInitWindowSize(s.width, s.height)
    glutInitWindowPosition(100, 100) 

    glutCreateWindow(sys.argv[0])

    setup()

    # mock callback functions that transfer to the simulator object
    def _draw():
        s.draw()
    def _mouseMotion(x, y):
        s.mouseMotion(x, y)
    def _mouseDragged(x, y):
        s.mouseDragged(x, y)
    def _mouseControl(button, state, x, y):
        s.mouseControl(button, state, x, y)
    def _keyboard_special(key, x, y):
        s.keyboard_special(key, x, y)
    def _keyboard(key, x, y):
        s.keyboard(key, x, y)
    def _resize(w, h):
        s.resize(w, h)

    glutDisplayFunc(_draw)
    glutKeyboardFunc(_keyboard)
    glutSpecialFunc(_keyboard_special)
    glutMouseFunc(_mouseControl)
    glutPassiveMotionFunc(_mouseMotion)
    glutMotionFunc(_mouseDragged)
    glutReshapeFunc(_resize);  
    glutMainLoop()
    return 0

if __name__ == '__main__':
    main()
