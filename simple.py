import itertools
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
    not_zero = pins_to_centroid != 0
    pins_eccentric_shear = (-torque / np.sum(np.square(pins_to_centroid[not_zero]) * pins_area[not_zero])) * pins_to_centroid * pins_area
    return pins_eccentric_shear
def shear_direction(pins_x_to_centroid, pins_y_to_centroid, pins_eccentric_shear, torque):
    rotated_x_to_centroid = -pins_y_to_centroid     # ccw rotation: counteracts cw torque
    rotated_y_to_centroid = pins_x_to_centroid
    if torque > 0:
        rotated_x_to_centroid *= -1
        rotated_y_to_centroid *= -1
    magnitudes = np.sqrt(np.square(rotated_x_to_centroid) + np.square(rotated_y_to_centroid))
    not_zero = magnitudes != 0
    unit_x, unit_y = np.zeros(np.size(pins_x_to_centroid)), np.zeros(np.size(pins_y_to_centroid))
    unit_x[not_zero] = rotated_x_to_centroid[not_zero] / magnitudes[not_zero]
    unit_y[not_zero] = rotated_y_to_centroid[not_zero] / magnitudes[not_zero]
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
    # print("Max Shear Stress: " + str(round(max_shear_stress, 3)) + " at Pin " + str(int(max_shear_pin)))
    # print(total_shear_stress)
    return max_shear_stress, max_shear_pin
def pin_test_optimization(load, load_x,  diameters, pins_tested, total_pins):
    pin_combinations = np.array(list(itertools.combinations(range(1, total_pins + 1), pins_tested)))
    all_max_shear_stresses, all_max_shear_pins = np.zeros(math.comb(total_pins, pins_tested)), np.zeros(math.comb(total_pins, pins_tested))
    for i in range(np.size(pin_combinations, axis=0)):
        all_max_shear_stresses[i], all_max_shear_pins[i] = pin_test(load, load_x, pin_combinations[i], diameters)
        print("Pin Config.: " + str(pin_combinations[i]) + "\n\tMax Stress: " + str(round(all_max_shear_stresses[i], 3)) + " at Pin " + str(pin_combinations[i][int(all_max_shear_pins[i])]))
def main():
    load = 1
    load_x = 0
    selection = [12, 13, 14, 15]
    diameters = [0.1875, 0.1875, 0.1875, 0.1875]
    pin_test_optimization(load, load_x, diameters, pins_tested = 4, total_pins = 15)
    # pin_test(load, load_x, selection, diameters)
if __name__ == '__main__':
    main()
