#!/usr/bin/env python2
from __future__ import division
import numpy as np
import io

class MatchedFilter():
    def __init__(self, cam_w, cam_h, fov,
                 orientation=[0.0, 0.0, 0.0],
                 axis=[0.0, 0.0, 0.0]):

        self.cam_w = cam_w
        self.cam_h = cam_h
        
        self.fovx, self.fovy = MatchedFilter._get_fov(fov)

        orientation = np.array(orientation, dtype=float)
        self.rot_mat = self._rotation_matrix(orientation)
        axis = np.array(axis, dtype=float)
        self.axis = np.matmul(self._rotation_matrix(axis).T, np.array([0, 0, 1]))
        self.D = self._get_viewing_directions(orientation)
        self.matched_filter = self.generate_filter()


    @staticmethod
    def _get_fov(fov):
        fovx, fovy = map(float, fov)
        if fovx == 365:
            fovx == 364
        if fovy == 180:
            fovy = 179
        return np.deg2rad(fovx), np.deg2rad(fovy)
    
    def _get_viewing_directions(self, orientation):
        vertical_views = (((np.arange(self.cam_h, dtype=float) -
                            self.cam_h / 2.0) / float(self.cam_h)) *
                          self.fovy)
        horizontal_views = (((np.arange(self.cam_w, dtype=float) -
                              self.cam_w / 2.0) / float(self.cam_w)) *
                            self.fovx)
        #vertical_views = ((np.arange(self.cam_h, dtype=float) - self.cam_h / 2.0) / float(self.cam_h)) * np.deg2rad(self.fovy)
        #horizontal_views = ((np.arange(self.cam_w, dtype=float) - self.cam_w / 2.0) / float(self.cam_w)) * np.deg2rad(self.fovx)

        D = np.ones([self.cam_h, self.cam_w, 3])
        D[:, :, 0], D[:, :, 1] = np.meshgrid(np.tan(horizontal_views),
                                             np.tan(vertical_views))
        D = self._rotate_viewing_directions(D, orientation)
        return D

    def _rotate_viewing_directions(self, D, orientation):
        for ii in range(self.cam_h):
            for jj in range(self.cam_w):
                D[ii, jj, :] = np.matmul(D[ii, jj, :], self.rot_mat)
        return D

    def _rotation_matrix(self, orientation):
        """
        In camera coordinates
          x - pitch
          y - roll
          z - yaw
        """
        pitch, roll, yaw = orientation
        rx = np.deg2rad(pitch)
        ry = np.deg2rad(roll)
        rz = np.deg2rad(yaw)

        Rx = np.array([[1, 0, 0], [0, np.cos(rx), -np.sin(rx)],
                       [0, np.sin(rx), np.cos(rx)]])
        Ry = np.array([[np.cos(ry), 0, np.sin(ry)], [0, 1, 0],
                       [-np.sin(ry), 0, np.cos(ry)]])
        Rz = np.array([[np.cos(rz), -np.sin(rz), 0],
                       [np.sin(rz), np.cos(rz), 0], [0, 0, 1]])

        rot_mat = np.matmul(np.matmul(Rx, Ry), Rz)
        return rot_mat
            
    def generate_filter(self):

        sin_theta = np.linalg.norm(self.D[:, :, 0:2], axis=2) + 1e-14
        sin_theta = np.repeat(sin_theta[:, :, np.newaxis], 2, axis=2)
        mag_temp = np.linalg.norm(self.D, axis=2)
        D = self.D / np.expand_dims(mag_temp, axis=2)
        
        mf = -np.cross(np.cross(D, self.axis), D)[:, :, 0:2] / sin_theta
        return mf

    def plot(self, show=False):
        """
        Plot the matched filters that have been generated by this class
        :return:
        """
        import matplotlib.pyplot as plt
        from matplotlib.figure import Figure
        if not show:
            fig = Figure()
            axis = fig.add_subplot(1, 1, 1)
            
        else:
            fig, axis = plt.subplots()

        Y = ((np.arange(self.cam_h, dtype=float) - self.cam_h / 2.0) / float(
            self.cam_h)) * np.rad2deg(self.fovy)

        X = ((np.arange(self.cam_w, dtype=float) - self.cam_w / 2.0) / float(
            self.cam_w)) * np.rad2deg(self.fovx)

        U = self.matched_filter[:, :, 0]
        V = self.matched_filter[:, :, 1]
        step_size = 20
        scale = None
        axis.set_xlabel('x (degrees)')
        axis.set_ylabel('y (degrees)')
        axis.quiver(X[::step_size], Y[::step_size],
                    U[::step_size, ::step_size],
                    V[::step_size, ::step_size],
                    pivot='mid', scale=scale)

        plt.show()
        return fig
    
    def  plot_D(self, show=False):
        import matplotlib.pyplot as plt
        from matplotlib.figure import Figure
        from mpl_toolkits.mplot3d import Axes3D
        print(self.rot_mat)
        V = np.matmul(np.linalg.inv(self.rot_mat), np.array([0, 0, 1]))
        if not show:
            fig = Figure()

        else:
            fig = plt.figure()
#        ax = Axes3d(fig)
        ax = fig.add_subplot(111, projection='3d')
        ax.set_xlim3d(-1, 1)
        ax.set_ylim3d(-1, 1)
        ax.set_zlim3d(-1, 1)
        ax.set_xlabel('X axis')
        ax.set_ylabel('Y axis')
        ax.set_zlabel('Z axis')
        ax.quiver(0, 0, 0, V[0], V[1], V[2], normalize=True)
        ax.quiver(0, 0, 0, self.axis[0], self.axis[1], self.axis[2], normalize=True)
        plt.show()
        return fig

    def get_unit_directions(self):

        def get_unit(v, shorter=1):
            return list(v / (np.linalg.norm(v) * shorter))

        return {
            'camx': get_unit(np.matmul(np.linalg.inv(self.rot_mat),
                                       np.array([1, 0, 0])), shorter=1.2),
            'camy': get_unit(np.matmul(np.linalg.inv(self.rot_mat),
                                       np.array([0, 1, 0])), shorter=1.2),
            'camz': get_unit(np.matmul(np.linalg.inv(self.rot_mat),
                                       np.array([0, 0, 1])), shorter=1.2),
            'axis': get_unit(self.axis)
        }

    def get_matched_filter_str(self):
        print(np.array_str(self.matched_filter))
        return np.array_str(self.matched_filter)


    
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Create matched filters')
    parser.add_argument('--width', type=int, default=640,
                        help="""Camera's width
                        Default: 640""")
    parser.add_argument('--height', type=int, default=360,
                        help="""Camera's height
                        Default: 300""")
    parser.add_argument('-f','--fov', nargs='+',
                        default=[180, 90],
                        help="""The x and y fov or intrinsic matrix,
                        either flattened or as a matrix.
                        Default: fovx: 90, 45""")
    parser.add_argument('-o', '--orientation', nargs='+', default=[0.0, 0.0, 0.0],
                        help="""Orientation of the camera. [yaw, pitch, roll]
                        Default [0.0, 0.0, 0.0]""")
    parser.add_argument('-a', '--axis', nargs='+', default=[0.0, 0.0, 0.0],
                        help="""Prefered axis of orientation
                        Default: [0.0, 0.0, 0.0]""")
    args = parser.parse_args()

    mf = MatchedFilter(args.width, args.height, args.fov, 
                       orientation=args.orientation,
                       axis=args.axis)
    mf.plot(show=True)

    mf.plot_D()

    


