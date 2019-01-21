from enum import Enum


class JoystickItem(object):

    def __init__(self, joystick, type, index1, index2=0):
        self.joystick = joystick
        self.type = type
        self.index1 = index1
        self.index2 = index2
        self.inverse_value = False

    def value(self):
        if self.type == JoystickItemType.axis:
            return self.joystick.get_axis(self.index1) * (-1 if self.inverse_value else 1)
        elif self.type == JoystickItemType.button:
            return self.joystick.get_button(self.index1) * (-1 if self.inverse_value else 1)
        elif self.type == JoystickItemType.hat:
            return self.joystick.get_hat(self.index1)[self.index2] * (-1 if self.inverse_value else 1)


class JoystickItemType(Enum):
    axis = 1
    button = 2
    hat = 3
