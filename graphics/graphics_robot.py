from graphics.graphics_canvas import *
from graphics.common_functions import wrap_to_pi


class DefaultJoint:
    """
    This class forms a base for all the different types of joints
    - Rotational
    - Prismatic
    - Static
    - Gripper

    :param connection_from_prev_seg: Origin point of the joint (Where it connects to the previous segment)
    :type connection_from_prev_seg: class:`vpython.vector`
    :param connection_to_next_seg: Tooltip point of the joint (Where it connects to the next segment)
    :type connection_to_next_seg: class:`vpython.vector`
    :param axis: Vector representation of the joints +x axis, defaults to +x axis (1, 0, 0)
    :type axis: class:`vpython.vector`
    :param graphic_object: Graphical object for which the joint will use. If none given, auto generates an object,
    defaults to `None`
    :type graphic_object: class:`vpython.compound`
    """

    def __init__(self,
                 connection_from_prev_seg,
                 connection_to_next_seg,
                 axis=vector(1, 0, 0),
                 graphic_object=None):
        # Set connection points
        self.__connect_from = connection_from_prev_seg
        self.__connect_to = connection_to_next_seg
        # Set an arrow to track position and direction for easy updates
        self.__connect_dir = arrow(pos=self.__connect_from,
                                   axis=(self.__connect_to - self.__connect_from),
                                   visible=False)
        # Set the x vector direction
        self.x_vector = axis
        self.x_rotation = radians(0)
        self.y_rotation = radians(0)
        self.z_rotation = radians(0)

        # Set the graphic
        self.__graphic_obj = self.__set_graphic(graphic_object)
        self.visible = True

        # Calculate the length of the link (Generally longest side is the length)
        self.__length = max(self.__graphic_obj.length, self.__graphic_obj.width, self.__graphic_obj.height)

        # Set the other reference frame vectors
        self.__graphic_ref = draw_reference_frame_axes(self.__connect_to, self.x_vector, self.x_rotation)
        self.__update_reference_frame()

        # Calculate the arm angle
        # self.arm_angle = self.calculate_arm_angle()

    def update_position(self, new_pos):
        """
        Move the position of the link to the specified location

        :param new_pos: 3D vector representing the new location for the origin (connection_from) of the link
        :type new_pos: class:`vpython.vector`
        """
        # Calculate translational movement amount
        axes_movement = new_pos - self.__connect_from
        # Update each position
        self.__connect_from += axes_movement
        self.__connect_to += axes_movement
        self.__connect_dir.pos += axes_movement
        # If the reference frame exists, redraw it
        if self.__graphic_ref is not None:
            self.draw_reference_frame(self.__graphic_ref.visible)
        self.__draw_graphic()

    def update_orientation(self, angle_of_rotation, axis_of_rotation):
        #
        if axis_of_rotation.equals(vector(1, 0, 0)):
            rotation_axis = self.x_vector
            self.x_rotation = wrap_to_pi(self.x_rotation + angle_of_rotation)
        elif axis_of_rotation.equals(vector(0, 1, 0)):
            rotation_axis = self.y_vector
            self.y_rotation = wrap_to_pi(self.y_rotation + angle_of_rotation)
        elif axis_of_rotation.equals(vector(0, 0, 1)):
            rotation_axis = self.z_vector
            self.z_rotation = wrap_to_pi(self.z_rotation + angle_of_rotation)
        else:
            rotation_axis = self.y_vector
            self.y_rotation = wrap_to_pi(self.y_rotation + angle_of_rotation)

        # TODO
        #  Get rotation working for all axis

        # Calculate the new vector representation the link will be at for the new angle
        #new_direction = self.x_vector.rotate(angle=angle_of_rotation, axis=rotation_axis)
        #if axis_of_rotation.equals(vector(1, 0, 0)):
        self.__graphic_obj.rotate(angle=angle_of_rotation, axis=rotation_axis, origin=self.__connect_from)
        # Update the vectors and reference frames
        self.__update_reference_frame()
        # Calculate the updated toolpoint location
        self.__connect_dir.rotate(angle=angle_of_rotation, axis=rotation_axis)
        self.__connect_to = self.__connect_dir.pos + self.__connect_dir.axis
        # If the reference frame exists, redraw it
        if self.__graphic_ref is not None:
            self.draw_reference_frame(self.__graphic_ref.visible)
        # Update object graphic
        self.__draw_graphic()

    def __update_reference_frame(self):
        """
        Update the reference frame axis vectors
        """
        # X vector is through the tooltip
        self.x_vector = self.__graphic_obj.axis
        self.x_vector.mag = self.__length
        # Y vector is in the 'up' direction of the object
        self.y_vector = self.__graphic_obj.up
        self.y_vector.mag = self.__length
        # Z vector is the cross product of the two
        self.z_vector = self.x_vector.cross(self.y_vector)
        self.z_vector.mag = self.__length

    def draw_reference_frame(self, is_visible):
        """
        Draw a reference frame at the tool point position
        :param is_visible: Whether the reference frame should be drawn or not
        :type is_visible: bool
        """
        # If not visible, turn off
        if not is_visible:
            # If a reference frame exists
            if self.__graphic_ref is not None:
                # Set invisible, and also update its orientations
                self.__graphic_ref.visible = False
                self.__graphic_ref.pos = self.__connect_to
                self.__graphic_ref.axis = self.x_vector
                self.__graphic_ref.up = self.y_vector
        # Else: draw
        else:
            # If graphic does not currently exist
            if self.__graphic_ref is None:
                # Create one
                self.__graphic_ref = draw_reference_frame_axes(self.__connect_to, self.x_vector, self.x_rotation)
            # Else graphic does exist
            else:
                self.__graphic_ref.pos = self.__connect_to
                self.__graphic_ref.axis = self.x_vector
                self.__graphic_ref.up = self.y_vector

    def __draw_graphic(self):
        """
        Draw the objects graphic on screen
        """
        self.__graphic_obj.pos = self.__connect_from
        self.__graphic_obj.axis = self.x_vector
        self.__graphic_obj.up = self.y_vector

    def set_joint_visibility(self, is_visible):
        if is_visible is not self.visible:
            self.__graphic_obj.visible = is_visible
            self.__graphic_ref.visible = is_visible
            self.visible = is_visible

    def __set_graphic(self, given_obj):
        """
        Set the graphic object depending on if one was given. If no object was given, create a box and return it

        :param given_obj: Graphical object for the joint
        :type given_obj: class:`vpython.compound`
        :return: New graphical object for the joint
        :rtype: class:`vpython.compound`
        """
        # If stl_filename is None, use a box
        if given_obj is None:
            box_midpoint = vector(
                (self.__connect_to - self.__connect_from).mag / 2,
                0,
                0
            )
            # NB: Set XY axis first, as vpython is +y up bias, objects rotate respective to this bias when setting axis
            graphic_obj = box(pos=vector(box_midpoint.x, box_midpoint.y, box_midpoint.z),
                              axis=vector(1, 0, 0),
                              size=vector((self.__connect_to - self.__connect_from).mag, 0.1, 0.1),
                              up=vector(0, 0, 1))
            #graphic_obj.axis = self.x_vector
            #graphic_obj.pos = box_midpoint
            #graphic_obj.rotate(self.x_rotation)
            graphic_obj = compound([graphic_obj], origin=vector(0, 0, 0), axis=vector(1, 0, 0))
            return graphic_obj
        else:
            # TODO When texture application available, put it here
            return given_obj

    def __import_texture(self):
        # TODO (much later)
        pass

    def get_connection_to_pos(self):
        return self.__connect_to

    def get_rotation_angle(self, axis):
        if axis.equals(vector(1, 0, 0)):
            return self.x_rotation
        elif axis.equals(vector(0, 1, 0)):
            return self.y_rotation
        elif axis.equals(vector(0, 0, 1)):
            return self.z_rotation
        else:
            return self.y_rotation

class RotationalJoint(DefaultJoint):
    """
    A rotational joint based off the default joint class

    :param connection_from_prev_seg: Origin point of the joint (Where it connects to the previous segment)
    :type connection_from_prev_seg: class:`vpython.vector`
    :param connection_to_next_seg: Tooltip point of the joint (Where it connects to the next segment)
    :type connection_to_next_seg: class:`vpython.vector`
    :param x_axis: Vector representation of the joints +x axis, defaults to +x axis (1, 0, 0)
    :type x_axis: class:`vpython.vector`
    TODO rotation_axis
    :param graphic_obj: Graphical object for which the joint will use. If none given, auto generates an object,
    defaults to `None`
    :type graphic_obj: class:`vpython.compound`
    """

    # TODO
    #  1. Add input parameters to determine the rotation axis
    #  2. Update functions to rotate around the correct axis
    #      a. When doing this, make sure reference frame is correct too (i.e. for base)

    def __init__(self,
                 connection_from_prev_seg,
                 connection_to_next_seg,
                 x_axis=vector(1, 0, 0),
                 rotation_axis=vector(0, 1, 0),
                 graphic_obj=None):
        # Call super init function
        super().__init__(connection_from_prev_seg, connection_to_next_seg, x_axis, graphic_obj)
        # TODO
        #  sanity check input
        self.rotation_axis = rotation_axis

    def rotate_joint(self, new_angle):
        """
        Rotate the joint to a given angle in range [-pi pi] (radians)

        :param new_angle: The new angle in range [-pi pi] that the link is to be rotated to.
        :type new_angle: float (radians)
        """
        # Wrap given angle to -pi to pi
        new_angle = wrap_to_pi(new_angle)
        current_angle = self.get_rotation_angle(self.rotation_axis)
        # Calculate amount to rotate the link
        angle_diff = wrap_to_pi(new_angle - current_angle)
        # Update the link
        self.update_orientation(angle_diff, self.rotation_axis)


class PrismaticJoint(DefaultJoint):
    # TODO
    def __init__(self, connection_from_prev_seg, connection_to_next_seg, x_axis, graphic_obj=None):
        super().__init__(connection_from_prev_seg, connection_to_next_seg, x_axis, graphic_obj)
        self.min_translation = None
        self.max_translation = None

    def translate_joint(self, new_translation):
        # TODO calculate new connectTo point, update relevant super() params
        # TODO Update graphic
        pass

    def rotate_joint(self, new_angle):
        pass


class StaticJoint(DefaultJoint):
    # TODO
    def __init__(self, connection_from_prev_seg, connection_to_next_seg, x_axis, graphic_obj=None):
        super().__init__(connection_from_prev_seg, connection_to_next_seg, x_axis, graphic_obj)

    def rotate_joint(self, new_angle):
        pass


class Gripper(DefaultJoint):
    # TODO
    def __init__(self, connection_from_prev_seg, connection_to_next_seg, x_axis, graphic_obj=None):
        super().__init__(connection_from_prev_seg, connection_to_next_seg, x_axis, graphic_obj)

    def rotate_joint(self, new_angle):
        pass


class Robot:
    # TODO:
    #  Have functions to update links,
    #  take in rotation, translation, etc, params
    def __init__(self, joints):
        self.joints = joints
        self.num_joints = len(joints)
        self.is_shown = True
        self.__create_robot()

    def __create_robot(self, ):
        self.__position_joints()

    def __position_joints(self):
        for joint_num in range(1, self.num_joints):
            self.joints[joint_num].update_position(self.joints[joint_num - 1].get_connection_to_pos())

    def set_robot_visibility(self, is_visible):
        if is_visible is not self.is_shown:
            for joint in self.joints:
                joint.set_joint_visibility(is_visible)
                self.is_shown = is_visible

    def set_reference_visibility(self, is_visible):
        for joint in self.joints:
            joint.draw_reference_frame(is_visible)
