#! /usr/bin/env python3
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from PIL.Image import *

# Rotations for the planet
z_rot, z_speed = 0.0, 0.6
# Rotations for the moon
moon_rot, moon_speed = 0.0, 0.3

# Properties for the Sky Dome
distance_limit = 200
sky_radius = distance_limit / 6
sky_center = [0.0, 0.0, 0.0]
# Safety radius: max distance from the "sky dome center"
safety_radius = sky_radius / 3

# Camera parameters
phi = 0.0
theta = 0.0
eye = [0.0, 0.0, 8.0]
eye_rotation_delta = 5


def load_textures(fn, has_alpha_channel=False):
    # 2 possible cases: image with or without alpha channel
    image = open(fn)

    ix = image.size[0]
    iy = image.size[1]
    if has_alpha_channel:
        image = image.convert("RGBA")
        image = image.tobytes("raw", "RGBA", 0, -1)
    else:
        image = image.tobytes("raw", "RGBX", 0, -1)

    # Create Texture
    new_texture = glGenTextures(1)
    # 2d texture (x and y size)
    glBindTexture(GL_TEXTURE_2D, new_texture)

    glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
    if has_alpha_channel:
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, ix, iy, 0, GL_RGBA, GL_UNSIGNED_BYTE, image)
    else:
        glTexImage2D(GL_TEXTURE_2D, 0, 3, ix, iy, 0, GL_RGBA, GL_UNSIGNED_BYTE, image)
    # set the texture's stretching properties
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    if has_alpha_channel:
        glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_REPLACE)
    else:
        glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_DECAL)

    return new_texture


def init(width, height):
    global quadratic, b612, little_prince, baobab, fox, moon, starmap

    # Enables Depth Testing.
    # Makes 3D drawing work when something is in front of something else
    glEnable(GL_DEPTH_TEST)

    # Enable smooth shading
    glShadeModel(GL_SMOOTH)

    b612 = load_textures("asteroid_texture.jpg")
    starmap = load_textures("starmap_texture.jpg")
    moon = load_textures("moon_texture.jpg")
    little_prince = load_textures("little_prince_render.png", True)
    baobab = load_textures("baobab_render.png", True)
    fox = load_textures("fox_render.png", True)

    # Set up quadratic and its normals for correct light shading
    quadratic = gluNewQuadric()
    gluQuadricNormals(quadratic, GLU_SMOOTH)  # Create Smooth Normals
    gluQuadricTexture(quadratic, GL_TRUE)  # Create Texture Coordinates

    glEnable(GL_TEXTURE_2D)

    glTexGeni(GL_S, GL_TEXTURE_GEN_MODE, GL_SPHERE_MAP)
    glTexGeni(GL_T, GL_TEXTURE_GEN_MODE, GL_SPHERE_MAP)

    # Set The Projection Matrix
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    # Calculate The Aspect Ratio Of The Window and set maximum draw distance
    gluPerspective(45.0, float(width) / float(height), 0.1, 5 * distance_limit)

    # Back to model view matrix
    glMatrixMode(GL_MODELVIEW)


# Function to set the position of object with respect to the center of the sky box
def set_position(target_longitude, target_latitude, target_height):
    # 1) Move to the sky box center
    glTranslatef(sky_center[0], sky_center[1], sky_center[2])

    # 2) Rotate around y by a degree of longitude - 90
    glRotatef(target_longitude - 90, 0.0, 1.0, 0.0)

    # 3) Rotate around z by a degree of latitude - 90
    glRotatef(target_latitude - 90, 0.0, 0.0, 1.0)

    # 4) Translate the reference system up to the desired height
    glTranslatef(0.0, target_height, 0.0)


# The function called when our window is resized (which shouldn't happen if you enable fullscreen, below)
def resize_scene(width, height):
    # Prevent A Divide By Zero If The Window Is Too Small
    if height == 0:
        height = 1

    # Reset The Current Viewport And Perspective Transformation
    glViewport(0, 0, width, height)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45.0, float(width) / float(height), 0.1, 100.0)
    glMatrixMode(GL_MODELVIEW)


def draw_asteroid():
    glBindTexture(GL_TEXTURE_2D, b612)

    glPushMatrix()
    glRotatef(90, 1.0, 0.0, 0.0)
    # Rotate The Sphere On It's Z Axis
    glRotatef(z_rot, 0.0, 0.0, 1.0)

    glEnable(GL_TEXTURE_2D)
    # Draw A Sphere With A Radius Of 1 And 32 Longitude And 32 Latitude Segments
    gluSphere(quadratic, 1, 32, 32)

    glPopMatrix()


def draw_little_prince():
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glEnable(GL_ALPHA_TEST)
    glAlphaFunc(GL_GREATER, 0.0)

    glBindTexture(GL_TEXTURE_2D, little_prince)

    glPushMatrix()
    set_position(90, 90, 0)
    glRotatef(-z_rot, 0.0, 1.0, 0.0)

    glBegin(GL_QUADS)  # Begin

    glTexCoord2f(0.0, 1.0)
    glVertex3f(1.5, -0.25, 0.0)
    glTexCoord2f(1.0, 1.0)
    glVertex3f(1.5, 0.25, 0.0)
    glTexCoord2f(1.0, 0.0)
    glVertex3f(1.0, 0.25, 0.0)
    glTexCoord2f(0.0, 0.0)
    glVertex3f(1.0, -0.25, 0.0)

    glEnd()  # End coordinates

    glPopMatrix()

    glDisable(GL_ALPHA_TEST)
    glDisable(GL_BLEND)


# Function to draw the baobab with the default value of 8 plans
def draw_baobab(num_of_plans=8):
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glEnable(GL_ALPHA_TEST)
    glAlphaFunc(GL_GREATER, 0.0)

    if num_of_plans <= 0:
        print("Si è scelto un numero non ammissibile di piani per il baobab!")
        print("Verrano usati 8 piani su cui disegnare il baobab come di default!")
        num_of_plans = 8

    angle = 0
    increment = 180 / num_of_plans
    for i in range(0, num_of_plans):
        glBindTexture(GL_TEXTURE_2D, baobab)

        glPushMatrix()

        glRotatef(-z_rot, 0.0, 1.0, 0.0)
        set_position(150, 60, 0)
        glRotatef(angle, 1.0, 0.0, 0.0)

        glBegin(GL_QUADS)  # Begin

        glTexCoord2f(0.0, 1.0)
        glVertex3f(3, -0.5, 0.0)
        glTexCoord2f(1.0, 1.0)
        glVertex3f(3, 0.5, 0.0)
        glTexCoord2f(1.0, 0.0)
        glVertex3f(1.0, 0.5, 0.0)
        glTexCoord2f(0.0, 0.0)
        glVertex3f(1.0, -0.5, 0.0)

        glEnd()  # End coordinates

        glPopMatrix()

        angle += increment

    glDisable(GL_ALPHA_TEST)
    glDisable(GL_BLEND)


def draw_fox():
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glEnable(GL_ALPHA_TEST)
    glAlphaFunc(GL_GREATER, 0.0)

    glBindTexture(GL_TEXTURE_2D, fox)

    glPushMatrix()

    glRotatef(-z_rot, 0.0, 1.0, 0.0)
    set_position(260, 120, 0)

    glBegin(GL_QUADS)  # Begin

    glTexCoord2f(0.0, 1.0)
    glVertex3f(1.5, -0.25, 0.0)
    glTexCoord2f(1.0, 1.0)
    glVertex3f(1.5, 0.25, 0.0)
    glTexCoord2f(1.0, 0.0)
    glVertex3f(1.0, 0.25, 0.0)
    glTexCoord2f(0.0, 0.0)
    glVertex3f(1.0, -0.25, 0.0)

    glEnd()  # End coordinates

    glPopMatrix()

    glDisable(GL_ALPHA_TEST)
    glDisable(GL_BLEND)


def draw_moon():
    glBindTexture(GL_TEXTURE_2D, moon)

    glPushMatrix()

    # rotation around the asteroid
    glRotatef(-moon_rot, 0.0, 1.0, 0.0)
    set_position(90, 0, 2)

    # revolution around the y axes
    glRotatef(90, 1.0, 0.0, 0.0)
    glRotatef(z_rot, 1.0, 0.0, 0.0)

    glEnable(GL_TEXTURE_2D)
    gluSphere(quadratic, 0.2, 32, 32)

    glPopMatrix()


def draw_sky_box():
    glBindTexture(GL_TEXTURE_2D, starmap)

    glPushMatrix()

    glRotatef(90, 1.0, 0.0, 0.0)
    gluSphere(quadratic, sky_radius, 128, 128)

    glPopMatrix()


def draw_scene():
    global z_rot, z_speed, moon_rot, moon_speed, quadratic, b612, little_prince, baobab, fox, moon, starmap

    # Clear The Screen And The Depth Buffer
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    # Reset The View
    glLoadIdentity()
    # Set the camera
    center = (
        eye[0] - math.sin(theta * 2 * math.pi / 360.0),
        eye[1] + math.sin(phi * 2 * math.pi / 360),
        eye[2] - math.cos(theta * 2 * math.pi / 360.0)
    )
    gluLookAt(
        eye[0], eye[1], eye[2],
        center[0], center[1], center[2],
        0.0, 1.0, 0.0
    )
    # Move Into The Screen
    glTranslatef(0.0, 0.0, -5.0)

    draw_sky_box()
    draw_asteroid()
    draw_little_prince()
    draw_baobab(4)
    draw_fox()
    draw_moon()

    z_rot += z_speed
    moon_rot += moon_speed

    #  since this is double buffered, swap the buffers to display what just got drawn.
    glutSwapBuffers()


def key_pressed(key, x, y):
    global eye, theta, phi, eye_rotation_delta
    eye_new = eye[:]
    theta_in_radians = theta * 2 * math.pi / 360.0
    phi_in_radians = phi * 2 * math.pi / 360.0

    if key == b'\x1b':
        sys.exit()

    if key == b'w':  # move forward
        eye_new[0] -= math.sin(theta_in_radians)
        eye_new[1] += math.sin(phi_in_radians)
        eye_new[2] -= math.cos(theta_in_radians)

    if key == b's':  # move back
        eye_new[0] += math.sin(theta_in_radians)
        eye_new[1] -= math.sin(phi_in_radians)
        eye_new[2] += math.cos(theta_in_radians)

    if key == b'a':  # move left
        eye_new[0] -= math.cos(theta_in_radians)
        eye_new[1] += math.sin(phi_in_radians)
        eye_new[2] += math.sin(theta_in_radians)

    if key == b'd':  # move right
        eye_new[0] += math.cos(theta_in_radians)
        eye_new[1] -= math.sin(phi_in_radians)
        eye_new[2] -= math.sin(theta_in_radians)

    distance_of_eye_new_from_sky_center = math.sqrt(
        (eye_new[0] - sky_center[0]) ** 2
        + (eye_new[1] - sky_center[1]) ** 2
        + (eye_new[2] - sky_center[2]) ** 2
    )

    if distance_of_eye_new_from_sky_center <= safety_radius:
        eye = eye_new
        glutPostRedisplay()
    return


def special_pressed(key, x, y):
    global theta, eye_rotation_delta, phi
    if key == GLUT_KEY_RIGHT:  # look right
        theta = (theta - eye_rotation_delta) % 360
        glutPostRedisplay()
        return
    if key == GLUT_KEY_LEFT:  # look left
        theta = (theta + eye_rotation_delta) % 360
        glutPostRedisplay()
        return
    if key == GLUT_KEY_UP and phi < 90:  # look up
        phi += eye_rotation_delta
        glutPostRedisplay()
        return
    if key == GLUT_KEY_DOWN and phi > -90:  # look down
        phi -= eye_rotation_delta
        glutPostRedisplay()
    return


def main():
    glutInit()

    # Select type of Display mode:
    #  Double buffer
    #  RGBA color
    #  Alpha components supported
    #  Depth buffer
    glutInitDisplayMode(GLUT_RGBA | GLUT_DOUBLE | GLUT_DEPTH)

    # get a 800 x 600 window
    glutInitWindowSize(800, 600)

    # the window starts at the upper left corner of the screen
    glutInitWindowPosition(100, 100)
    glutCreateWindow("Asteroid B612")

    # Register the drawing function with glut, BUT in Python land, at least using PyOpenGL, we need to
    # set the function pointer and invoke a function to actually register the callback, otherwise it
    # would be very much like the C version of the code.
    glutDisplayFunc(draw_scene)

    # Uncomment this line to get full screen.
    # glutFullScreen()

    # When we are doing nothing, redraw the scene.
    glutIdleFunc(draw_scene)

    # Register the function called when our window is re-sized
    glutReshapeFunc(resize_scene)

    # Register the function called when the keyboard is pressed
    glutKeyboardFunc(key_pressed)
    glutSpecialFunc(special_pressed)

    # Initialize our window.
    init(800, 600)

    # Start Event Processing Engine
    glutMainLoop()


# Print message to console, and kick off the main to get it rolling.
if __name__ == "__main__":
    print("Press W A S D keys to move the observer in space")
    print("Press the arrow keys to change the camera orientation")
    print("Press the ESC key to quit")
    main()
