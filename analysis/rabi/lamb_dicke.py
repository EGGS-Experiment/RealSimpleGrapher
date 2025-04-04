from numpy import pi, abs, cos
from labrad import units as U, types as T


class lamb_dicke(object):

    @classmethod
    def lamb_dicke(self, trap_frequency, projection_angle, laser_wavelength=729e-9, amumass=40):
        '''
        Computes the lamb-dicke parameter.
        @var theta: angle between the laser and the mode of motion. 90 degrees is perpendicular
        @var laser_wavelength: laser wavelength
        @var trap_frequency: trap frequency
        @amumass particle mass in amu
        '''
        theta = projection_angle
        frequency = trap_frequency
        mass = amumass * U.amu
        k = 2. * pi / laser_wavelength
        eta = k * (U.hbar / (2 * mass * 2 * pi * frequency)) ** .5 * abs(cos(theta * 2. * pi / 360.0))
        #eta = eta.inBaseUnits().value
        return eta


if __name__ == '__main__':
    trap_frequency = 30e6
    projection_angle = 45  # degrees
    eta = lamb_dicke.lamb_dicke(trap_frequency, projection_angle)
    print('eta {}'.format(eta))
