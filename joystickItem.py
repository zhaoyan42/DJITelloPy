from enum import Enum


class JoystickItem(object):

    def __init__(self, joystick, type, index1, index2=0):
        self.joystick = joystick
        self.type = type
        self.index1 = index1
        self.index2 = index2

    def value(self):
        if self.type == JoystickItemType.axis:
            return self.joystick.get_axis(self.index1)
        elif self.type == JoystickItemType.button:
            return self.joystick.get_button(self.index1)
        elif self.type == JoystickItemType.hat:
            return self.joystick.get_hat(self.index1)[self.index2]


class JoystickItemType(Enum):
    axis = 1
    button = 2
    hat = 3
