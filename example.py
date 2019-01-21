from djitellopy import Tello
from joystickItem import JoystickItem, JoystickItemType
import cv2
import pygame
from pygame.locals import *
import numpy as np
import time

# Speed of the drone
S = 60
# Frames per second of the pygame window display
FPS = 25


class FrontEnd(object):
    """ Maintains the Tello display and moves it through the keyboard keys.
        Press escape key to quit.
        The controls are:
            - T: Takeoff
            - L: Land
            - Arrow keys: Forward, backward, left and right.
            - A and D: Counter clockwise and clockwise rotations
            - W and S: Up and down.
    """

    def __init__(self):
        # Init pygame
        pygame.init()
        pygame.joystick.init()

        self.joystick_count = pygame.joystick.get_count()
        if self.joystick_count > 0:
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()

            self.left_right_item = JoystickItem(
                self.joystick, JoystickItemType.axis, 0)
            self.for_back_item = JoystickItem(
                self.joystick, JoystickItemType.axis, 1)
            self.for_back_item.inverse_value = True
            self.yaw_item = JoystickItem(
                self.joystick, JoystickItemType.axis, 3)

            self.speed_item = JoystickItem(
                self.joystick, JoystickItemType.axis, 2)
            self.speed_item.inverse_value = True

            self.up_down_item_type = JoystickItemType.button
            self.up_item = JoystickItem(
                self.joystick, JoystickItemType.button, 4)
            self.down_item = JoystickItem(
                self.joystick, JoystickItemType.button, 2)

            self.flip_f_item = JoystickItem(
                self.joystick, JoystickItemType.hat, 0, 1)
            self.flip_b_item = JoystickItem(
                self.joystick, JoystickItemType.hat, 0, 1)
            self.flip_b_item.inverse_value = True
            self.flip_l_item = JoystickItem(
                self.joystick, JoystickItemType.hat, 0, 0)
            self.flip_l_item.inverse_value = True
            self.flip_r_item = JoystickItem(
                self.joystick, JoystickItemType.hat, 0, 0)

            # self.up_down_item_type = JoystickItemType.hat
            # self.up_down_item = JoystickItem(
            #     self.joystick, JoystickItemType.hat, 0, 1)

            self.takeoff_item = JoystickItem(
                self.joystick, JoystickItemType.button, 11)
            self.land_item = JoystickItem(
                self.joystick, JoystickItemType.button, 10)
            self.emergency_item = JoystickItem(
                self.joystick, JoystickItemType.button, 3)

        # Creat pygame window
        pygame.display.set_caption("Tello video stream")
        self.screen = pygame.display.set_mode([960, 720])

        # Init Tello object that interacts with the Tello drone
        self.tello = Tello()

        # Drone velocities between -100~100
        self.for_back_velocity = 0
        self.left_right_velocity = 0
        self.up_down_velocity = 0
        self.yaw_velocity = 0
        self.speed = 10

        self.send_rc_control = False

        # create update timer
        pygame.time.set_timer(USEREVENT + 1, 50)

    def run(self):

        if not self.tello.connect():
            print("Tello not connected")
            return

        if not self.tello.set_speed(self.speed):
            print("Not set speed to lowest possible")
            return

        # In case streaming is on. This happens when we quit this program
        # without the escape key.
        if not self.tello.streamoff():
            print("Could not stop video stream")
            return

        if not self.tello.streamon():
            print("Could not start video stream")
            return

        frame_read = self.tello.get_frame_read()

        should_stop = False
        while not should_stop:

            self.set_value_by_joystick()

            for event in pygame.event.get():
                if event.type == USEREVENT + 1:
                    self.update()
                elif event.type == QUIT:
                    should_stop = True
                elif event.type == KEYDOWN:
                    if event.key == K_ESCAPE:
                        should_stop = True
                    else:
                        self.keydown(event.key)
                elif event.type == KEYUP:
                    self.keyup(event.key)
                elif event.type == pygame.JOYBUTTONDOWN:
                    self.buttondown(event.button)
                elif event.type == pygame.JOYBUTTONUP:
                    self.buttonup(event.button)
                if event.type == pygame.JOYHATMOTION:
                    self.hatmotion(event.hat, event.value)

            if frame_read.stopped:
                frame_read.stop()
                break

            self.screen.fill([0, 0, 0])
            frame = cv2.cvtColor(frame_read.frame, cv2.COLOR_BGR2RGB)
            frame = np.rot90(frame)
            frame = np.flipud(frame)
            frame = pygame.surfarray.make_surface(frame)
            self.screen.blit(frame, (0, 0))
            pygame.display.update()

            time.sleep(1 / FPS)

        # Call it always before finishing. I deallocate resources.
        self.tello.end()

    def set_value_by_joystick(self):
        if self.joystick_count > 0:
            speed = (self.speed_item.value() + 1) / 2 * 100
            self.left_right_velocity = int(
                speed * self.left_right_item.value())
            self.for_back_velocity = int(speed * self.for_back_item.value())
            self.yaw_velocity = int(speed * self.yaw_item.value())
            if self.up_down_item_type == JoystickItemType.button:
                self.up_down_velocity = int(
                    speed * (self.up_item.value() - self.down_item.value()))
            elif self.up_down_item_type == JoystickItemType.hat:
                self.up_down_velocity = int(speed * self.up_down_item.value())

    def buttondown(self, button):
        if button == self.takeoff_item.index1:
            self.tello.takeoff()
            self.send_rc_control = True
        elif button == self.emergency_item.index1:
            self.tello.emergency()
            self.send_rc_control = False

    def buttonup(self, button):
        if button == self.land_item.index1:
            self.tello.land()
            self.send_rc_control = False

    def hatmotion(self, hat, value):
        if self.hat_item_motioned(hat, value, self.flip_f_item):
            self.tello.flip_forward()
        elif self.hat_item_motioned(hat, value, self.flip_b_item):
            self.tello.flip_back()
        elif self.hat_item_motioned(hat, value, self.flip_r_item):
            self.tello.flip_right()
        elif self.hat_item_motioned(hat, value, self.flip_l_item):
            self.tello.flip_left()

    def hat_item_motioned(self, hat, value, hat_item):
        return hat == hat_item.index1 and value[hat_item.index2] * \
            (-1 if hat_item.inverse_value else 1) > 0

    def keydown(self, key):
        """ Update velocities based on key pressed
        Arguments:
            key: pygame key
        """
        if key == pygame.K_UP:  # set forward velocity
            self.for_back_velocity = S
        elif key == pygame.K_DOWN:  # set backward velocity
            self.for_back_velocity = -S
        elif key == pygame.K_LEFT:  # set left velocity
            self.left_right_velocity = -S
        elif key == pygame.K_RIGHT:  # set right velocity
            self.left_right_velocity = S
        elif key == pygame.K_w:  # set up velocity
            self.up_down_velocity = S
        elif key == pygame.K_s:  # set down velocity
            self.up_down_velocity = -S
        elif key == pygame.K_a:  # set yaw clockwise velocity
            self.yaw_velocity = -S
        elif key == pygame.K_d:  # set yaw counter clockwise velocity
            self.yaw_velocity = S

    def keyup(self, key):
        """ Update velocities based on key released
        Arguments:
            key: pygame key
        """
        if key == pygame.K_UP or key == pygame.K_DOWN:  # set zero forward/backward velocity
            self.for_back_velocity = 0
        elif key == pygame.K_LEFT or key == pygame.K_RIGHT:  # set zero left/right velocity
            self.left_right_velocity = 0
        elif key == pygame.K_w or key == pygame.K_s:  # set zero up/down velocity
            self.up_down_velocity = 0
        elif key == pygame.K_a or key == pygame.K_d:  # set zero yaw velocity
            self.yaw_velocity = 0
        elif key == pygame.K_t:  # takeoff
            self.tello.takeoff()
            self.send_rc_control = True
        elif key == pygame.K_l:  # land
            self.tello.land()
            self.send_rc_control = False

    def update(self):
        """ Update routine. Send velocities to Tello."""
        if self.send_rc_control:
            self.tello.send_rc_control(self.left_right_velocity, self.for_back_velocity, self.up_down_velocity,
                                       self.yaw_velocity)


def main():
    frontend = FrontEnd()

    # run frontend
    frontend.run()


if __name__ == '__main__':
    main()
