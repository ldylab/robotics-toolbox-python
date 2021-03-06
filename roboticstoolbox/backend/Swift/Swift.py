#!/usr/bin/env python
"""
@author Jesse Haviland
"""

import os
from subprocess import call, Popen
from roboticstoolbox.backend.Connector import Connector
import zerorpc
import roboticstoolbox as rp
import numpy as np
import spatialmath as sm


class Swift(Connector):  # pragma nocover

    def __init__(self):
        super(Swift, self).__init__()

        # Popen(['npm', 'start', '--prefix', os.environ['SIM_ROOT']])

    #
    #  Basic methods to do with the state of the external program
    #

    def launch(self):
        '''
        env = launch(args) launch the external program with an empty or
        specific scene as defined by args

        '''

        super().launch()

        self.robots = []
        self.shapes = []

        self.swift = zerorpc.Client()
        self.swift.connect("tcp://127.0.0.1:4242")

    def step(self, dt=50):
        '''
        state = step(args) triggers the external program to make a time step
        of defined time updating the state of the environment as defined by
        the robot's actions.

        The will go through each robot in the list and make them act based on
        their control type (position, velocity, acceleration, or torque). Upon
        acting, the other three of the four control types will be updated in
        the internal state of the robot object. The control type is defined
        by the robot object, and not all robot objects support all control
        types.

        '''

        super().step

        self._step_robots(dt)
        self._step_shapes(dt)

        # self._draw_ellipses()
        self._draw_all()

    def reset(self):
        '''
        state = reset() triggers the external program to reset to the
        original state defined by launch

        '''

        super().reset

    def restart(self):
        '''
        state = restart() triggers the external program to close and relaunch
        to thestate defined by launch

        '''

        super().restart

    def close(self):
        '''
        state = close() triggers the external program to gracefully close

        '''

        super().close()

    #
    #  Methods to interface with the robots created in other environemnts
    #

    def add(self, ob, show_robot=True, show_collision=False):
        '''
        id = add(robot) adds the robot to the external environment. robot must
        be of an appropriate class. This adds a robot object to a list of
        robots which will act upon the step() method being called.

        '''

        super().add()

        if isinstance(ob, rp.ERobot):
            robot = ob.to_dict()
            robot['show_robot'] = show_robot
            robot['show_collision'] = show_collision
            id = self.swift.robot(robot)
            self.robots.append(ob)
            return id
        elif isinstance(ob, rp.Shape):
            shape = ob.to_dict()
            id = self.swift.shape(shape)
            self.shapes.append(ob)
            return id

    def remove(self):
        '''
        id = remove(robot) removes the robot to the external environment.

        '''

        super().remove()

    def _step_robots(self, dt):

        for robot in self.robots:

            # if rpl.readonly or robot.control_type == 'p':
            #     pass            # pragma: no cover

            if robot.control_type == 'v':

                for i in range(robot.n):
                    robot.q[i] += robot.qd[i] * (dt / 1000)

                    if np.any(robot.qlim[:, i] != 0) and \
                            not np.any(np.isnan(robot.qlim[:, i])):
                        robot.q[i] = np.min([robot.q[i], robot.qlim[1, i]])
                        robot.q[i] = np.max([robot.q[i], robot.qlim[0, i]])

            elif robot.control_type == 'a':
                pass

            else:            # pragma: no cover
                # Should be impossible to reach
                raise ValueError(
                    'Invalid robot.control_type. '
                    'Must be one of \'p\', \'v\', or \'a\'')

    def _step_shapes(self, dt):

        for shape in self.shapes:

            T = shape.base
            t = T.t
            r = T.rpy('rad')

            t += shape.v[:3] * (dt / 1000)
            r += shape.v[3:] * (dt / 1000)

            shape.base = sm.SE3(t) * sm.SE3.RPY(r)

    def _draw_all(self):

        for i in range(len(self.robots)):
            self.robots[i].fkine_all()
        #     self.swift.robot_poses([i, self.robots[i].fk_dict()])

        # for i in range(len(self.shapes)):
        #     self.swift.shape_poses([i, self.shapes[i].fk_dict()])

    def record_start(self, file):
        self.swift.record_start(file)

    def record_stop(self):
        self.swift.record_stop(1)
