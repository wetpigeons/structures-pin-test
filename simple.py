import math
import numpy as np
def pin_info(selection, diameters):
    pins = np.array(selection)
    pins_diameters = np.array(diameters)
    pins_area = np.array(math.pi * (pins_diameters ** 2) / 4)
    pins_x = np.array(((pins - 1) % 3) * 0.5) + 1.5
    pins_y = np.array(((pins - 1) // 3) * 0.5)
    return pins, pins_x, pins_y, pins_area
def centroid_and_torque(pins_x, pins_y, pins_area, load, load_x):
    total_numerator_x = np.sum(pins_x * pins_area)
    total_numerator_y = np.sum(pins_y * pins_area)
    total_area = np.sum(pins_area)
    centroid = ((total_numerator_x/total_area),(total_numerator_y/total_area))
    load_offset = load_x - centroid[0]
    torque = load_offset * load
    return centroid, torque, load_offset
def dist_from_centroid(pins_x, pins_y, centroid):
    pins_x_to_centroid = pins_x - centroid[0]
    pins_y_to_centroid = pins_y - centroid[1]
    pins_to_centroid = np.sqrt(np.square(pins_x_to_centroid) + np.square(pins_y_to_centroid))
    return pins_to_centroid, pins_x_to_centroid, pins_y_to_centroid
def find_eccentric_shear_force(pins_to_centroid, pins_area, torque):
    pins_eccentric_shear = (-torque / np.sum(np.square(pins_to_centroid) * pins_area)) * pins_to_centroid * pins_area
    return pins_eccentric_shear
def shear_direction(pins_x_to_centroid, pins_y_to_centroid, pins_eccentric_shear, torque):
    rotated_x_to_centroid = -pins_y_to_centroid
    rotated_y_to_centroid = pins_x_to_centroid
    if torque < 0:
        rotated_x_to_centroid *= -1
        rotated_y_to_centroid *= -1
    magnitudes = np.sqrt(np.square(rotated_x_to_centroid) + np.square(rotated_y_to_centroid))
    unit_x = rotated_x_to_centroid / magnitudes     # potential divide by 0
    unit_y = rotated_y_to_centroid / magnitudes     # potential divide by 0
    pins_eccentric_shear_x = unit_x * pins_eccentric_shear
    pins_eccentric_shear_y = unit_y * pins_eccentric_shear
    return pins_eccentric_shear_x, pins_eccentric_shear_y
def find_total_shear_stress(pins_eccentric_shear_x, pins_eccentric_shear_y, load, pins_area, double_shear = True):
    total_area = np.sum(pins_area)
    total_shear_force_x = pins_eccentric_shear_x
    total_shear_force_y = pins_eccentric_shear_y - load * (pins_area / total_area)
    total_shear_force = np.sqrt(np.square(total_shear_force_x) + np.square(total_shear_force_y))
    if double_shear:
        total_shear_stress = total_shear_force / (2 * pins_area)
    else:
        total_shear_stress = total_shear_force / pins_area
    max_shear_stress = np.max(total_shear_stress)
    max_shear_pin = np.argmax(total_shear_stress)
    return max_shear_stress, max_shear_pin, total_shear_stress
def pin_test(load, load_x, selection, diameters):
    pins, pins_x, pins_y, pins_area = pin_info(selection, diameters)
    centroid, torque, load_offset = centroid_and_torque(pins_x, pins_y, pins_area, load, load_x)
    pins_to_centroid, pins_x_to_centroid, pins_y_to_centroid = dist_from_centroid(pins_x, pins_y, centroid)
    pins_eccentric_shear = find_eccentric_shear_force(pins_to_centroid, pins_area, torque)
    pins_eccentric_shear_x, pins_eccentric_shear_y = shear_direction(pins_x_to_centroid, pins_y_to_centroid, pins_eccentric_shear, torque)
    max_shear_stress, max_shear_pin, total_shear_stress = find_total_shear_stress(pins_eccentric_shear_x, pins_eccentric_shear_y, load, pins_area, double_shear=True)
    print("Max Shear Stress: " + str(round(max_shear_stress, 3)) + " at Pin " + str(int(max_shear_pin)))
    print(total_shear_stress)
def main():
    load = 1
    load_x = 0
    selection = [4, 6, 10, 12]
    diameters = [0.1875, 0.1875, 0.1875, 0.1875]
    pin_test(load, load_x, selection, diameters)
if __name__ == '__main__':
    main()
