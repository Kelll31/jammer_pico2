"""
Алгоритм калибровки тачскрина.
Порт msp2807_calibration.c.
"""

import math

class CalibrationMat:
    def __init__(self):
        self.KX1 = 0.0
        self.KX2 = 0.0
        self.KX3 = 0.0
        self.KY1 = 0.0
        self.KY2 = 0.0
        self.KY3 = 0.0

def calculate_calibration_mat(ref_points, sample_points):
    """
    Рассчитывает матрицу калибровки на основе массивов точек.

    ref_points: Список кортежей [(x0, y0), (x1, y1), ...] эталонных экранных точек
    sample_points: Список кортежей [(xs0, ys0), (xs1, ys1), ...] сырых точек из тачскрина

    Возвращает объект CalibrationMat или None в случае ошибки.
    """
    npoints = len(ref_points)

    if npoints < 3 or len(sample_points) != npoints:
        return None

    cmat = CalibrationMat()

    if npoints == 3:
        a = [0.0] * 3
        b = [0.0] * 3
        c = [0.0] * 3
        d = [0.0] * 3

        for i in range(3):
            a[i] = float(sample_points[i][0])
            b[i] = float(sample_points[i][1])
            c[i] = float(ref_points[i][0])
            d[i] = float(ref_points[i][1])

        k = (a[0]-a[2])*(b[1]-b[2]) - (a[1]-a[2])*(b[0]-b[2])
        if abs(k) < 1e-9:
            return None

        kM1 = 1.0 / k

        cmat.KX1 = ((c[0]-c[2])*(b[1]-b[2]) - (c[1]-c[2])*(b[0]-b[2])) * kM1
        cmat.KX2 = ((c[1]-c[2])*(a[0]-a[2]) - (c[0]-c[2])*(a[1]-a[2])) * kM1
        cmat.KX3 = (b[0]*(a[2]*c[1]-a[1]*c[2]) + b[1]*(a[0]*c[2]-a[2]*c[0]) + b[2]*(a[1]*c[0]-a[0]*c[1])) * kM1

        cmat.KY1 = ((d[0]-d[2])*(b[1]-b[2]) - (d[1]-d[2])*(b[0]-b[2])) * kM1
        cmat.KY2 = ((d[1]-d[2])*(a[0]-a[2]) - (d[0]-d[2])*(a[1]-a[2])) * kM1
        cmat.KY3 = (b[0]*(a[2]*d[1]-a[1]*d[2]) + b[1]*(a[0]*d[2]-a[2]*d[0]) + b[2]*(a[1]*d[0]-a[0]*d[1])) * kM1

        return cmat

    elif npoints > 3:
        a = [0.0] * 3
        b = [0.0] * 3
        c = [0.0] * 3
        d = [0.0] * 3

        fnpointsM1 = 1.0 / float(npoints)

        for i in range(npoints):
            a[2] += float(sample_points[i][0])
            b[2] += float(sample_points[i][1])
            c[2] += float(ref_points[i][0])
            d[2] += float(ref_points[i][1])

            a[0] += float(sample_points[i][0]) * float(sample_points[i][0])
            a[1] += float(sample_points[i][0]) * float(sample_points[i][1])

            b[0] = a[1]
            b[1] += float(sample_points[i][1]) * float(sample_points[i][1])

            c[0] += float(sample_points[i][0]) * float(ref_points[i][0])
            c[1] += float(sample_points[i][1]) * float(ref_points[i][0])

            d[0] += float(sample_points[i][0]) * float(ref_points[i][1])
            d[1] += float(sample_points[i][1]) * float(ref_points[i][1])

        if abs(a[2]) < 1e-9 or abs(b[2]) < 1e-9:
            return None

        a[0] = a[0] / a[2]
        a[1] = a[1] / b[2]
        b[0] = b[0] / a[2]
        b[1] = b[1] / b[2]
        c[0] = c[0] / a[2]
        c[1] = c[1] / b[2]
        d[0] = d[0] / a[2]
        d[1] = d[1] / b[2]

        a[2] = a[2] * fnpointsM1
        b[2] = b[2] * fnpointsM1
        c[2] = c[2] * fnpointsM1
        d[2] = d[2] * fnpointsM1

        k = (a[0]-a[2])*(b[1]-b[2]) - (a[1]-a[2])*(b[0]-b[2])
        if abs(k) < 1e-9:
            return None

        kM1 = 1.0 / k

        cmat.KX1 = ((c[0]-c[2])*(b[1]-b[2]) - (c[1]-c[2])*(b[0]-b[2])) * kM1
        cmat.KX2 = ((c[1]-c[2])*(a[0]-a[2]) - (c[0]-c[2])*(a[1]-a[2])) * kM1
        cmat.KX3 = (b[0]*(a[2]*c[1]-a[1]*c[2]) + b[1]*(a[0]*c[2]-a[2]*c[0]) + b[2]*(a[1]*c[0]-a[0]*c[1])) * kM1

        cmat.KY1 = ((d[0]-d[2])*(b[1]-b[2]) - (d[1]-d[2])*(b[0]-b[2])) * kM1
        cmat.KY2 = ((d[1]-d[2])*(a[0]-a[2]) - (d[0]-d[2])*(a[1]-a[2])) * kM1
        cmat.KY3 = (b[0]*(a[2]*d[1]-a[1]*d[2]) + b[1]*(a[0]*d[2]-a[2]*d[0]) + b[2]*(a[1]*d[0]-a[0]*d[1])) * kM1

        return cmat

    return None

def touch_transform_coords(cmat, px, py):
    """
    Преобразует координаты [px, py] из тачскрина в экранные.

    Возвращает кортеж: (экранный_x, экранный_y)
    """
    if cmat is None:
        return px, py

    d1024 = 1.0 / 1024.0

    new_px = int(d1024 * cmat.KX1 * float(px) + d1024 * cmat.KX2 * float(py) + cmat.KX3 + 0.5)
    new_py = int(d1024 * cmat.KY1 * float(px) + d1024 * cmat.KY2 * float(py) + cmat.KY3 + 0.5)

    return new_px, new_py
