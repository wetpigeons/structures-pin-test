import itertools
import math
import time

import numpy as np

def main():
    pins_tested = 4
    diameters = [0.1875 for _ in range(pins_tested)]
    available_diameters = [0.0625, 0.078125, 0.09375, 0.125, 0.140625, 0.15625, 0.1875, 0.21875, 0.25]
    total_pins = 15
    selection = [4, 6, 10, 12]
    load_x = 0
    load = 1
    shear = 2
    big = True
    bigger = False
    diameter_combinations = [diameters]
    diams = 1
    pin_combinations = [selection]
    combs = 1
    if big:
        pin_combinations = list(itertools.combinations(range(1, total_pins + 1), pins_tested))
        combs = math.comb(total_pins, pins_tested)
        if bigger:
            diameter_combinations = list(itertools.product(available_diameters, repeat=pins_tested))
            diams = len(available_diameters) ** pins_tested

    #     pin, x, y, diameters, area, x to centroid, y to centroid, to centroid, eccentric_shear, shear x, shear y, total shear y, total stress
    #     14 columns, # of pins being tested rows. # all pin combos deep. 4D for varying diameters
    pins = np.zeros((diams, combs, pins_tested, 15))
    for k in range(len(diameter_combinations)):
        for i in range(len(pin_combinations)):
            for j in range(pins_tested):
                pins[k, i, j, 0] = pin_combinations[i][j]     # pin #s
                pins[k, i, j, 3] = diameter_combinations[k][j]     # pin diameters

    pins[:, :, :, 1] = ((pins[:, :, :, 0] - 1) % 3) * 0.5 + 1.5   # pin_x
    pins[:, :, :, 2] = ((pins[:, :, :, 0] - 1) // 3) * 0.5        # pin_y
    pins[:, :, :, 4] = math.pi * np.square(pins[:, :, :, 3]) / 4  # pin_area
    total_area = np.sum(pins[:, :, :, 4], axis=2)[:, :, None]
    #
    # centroid = (np.sum(pins[:, :, :, 1]*pins[:, :, :, 4])/np.sum(pins[:, :, :, 4]), np.sum(pins[:, :, :, 2]*pins[:, :, :, 4])/np.sum(pins[:, :, :, 4]))
    pins[:, :, 0, 14] = np.sum(pins[:, :, :, 1]*pins[:, :, :, 4], axis=2)/np.sum(pins[:, :, :, 4], axis=2)
    pins[:, :, 1, 14] = np.sum(pins[:, :, :, 2]*pins[:, :, :, 4], axis=2)/np.sum(pins[:, :, :, 4], axis=2)

    pins[:, :, 2, 14] = load_x - pins[:, :, 0, 14]      # load offset
    pins[:, :, 3, 14] = pins[:, :, 2, 14] * load        # torque

    pins[:, :, :, 5] = pins[:, :, :, 1] - pins[:, :, 0, 14][:, :, None]       # pin x to centroid
    pins[:, :, :, 6] = pins[:, :, :, 2] - pins[:, :, 1, 14][:, :, None]       # pin y to centroid
    pins[:, :, :, 7] = np.sqrt(np.square(pins[:, :, :, 5])+np.square(pins[:, :, :, 6]))     # pin total to centroid
    #
    with np.errstate(divide='ignore', invalid='ignore'):
        pins[:, :, :, 8] = (-pins[:, :, 3, 14][:, :, None] / np.sum(np.square(pins[:, :, :, 7]) * pins[:, :, :, 4], axis=2)[:, :, None]) * pins[:, :, :, 7] * pins[:, :, :, 4]     # eccentric shear
        pins = np.nan_to_num(pins, nan=0.0, posinf=0.0, neginf=0.0)

    tmp = pins[:, :, :, 5].copy()
    pins[:, :, :, 5] = -1 * pins[:, :, :, 6]
    pins[:, :, :, 6] = tmp

    pins[:, :, :, 5][pins[:, :, 3, 14] > 0] *= -1
    pins[:, :, :, 6][pins[:, :, 3, 14] > 0] *= -1
    with np.errstate(divide='ignore', invalid='ignore'):
        pins[:, :, :, 9] = pins[:, :, :, 5] / np.sqrt(np.square(pins[:, :, :, 5]) + np.square(pins[:, :, :, 6])) * pins[:, :, :, 8]     # eccentric shear x
        pins[:, :, :, 10] = pins[:, :, :, 6] / np.sqrt(np.square(pins[:, :, :, 5]) + np.square(pins[:, :, :, 6])) * pins[:, :, :, 8]    # eccentric shear y
        pins = np.nan_to_num(pins, nan=0.0, posinf=0.0, neginf=0.0)

    pins[:, :, :, 11] = pins[:, :, :, 10] - load * (pins[:, :, :, 4] / total_area)      # total shear force y
    pins[:, :, :, 12] = np.sqrt(np.square(pins[:, :, :, 9]) + np.square(pins[:, :, :, 11]))     # total shear force
    pins[:, :, :, 13] = pins[:, :, :, 12] / (shear * pins[:, :, :, 4])

    np.set_printoptions(precision=3, floatmode='maxprec', suppress=True)
    if big and not bigger:
        largest_stress = np.max(np.max(pins[:,:,:,13], axis=2))
        largest_stress_indices = np.where(pins[:,:,:,13] == largest_stress)
        print(f'Largest Shear Stress (Earliest Failure): {round(largest_stress, 3)}, '
              f'at pin configuration(s):\n'
              f'{pins[largest_stress_indices[0], largest_stress_indices[1], :, 0]}')
        print(f'At pin(s): {pins[largest_stress_indices[0], largest_stress_indices[1], largest_stress_indices[2], 0]} respectively.\n')
        lowest_max_stress = np.min(np.max(pins[:, :, :, 13], axis=2))
        lowest_max_stress_indices = np.where(pins[:, :, :, 13] == lowest_max_stress)
        print(f'Lowest Max Shear Stress: {round(lowest_max_stress, 3)}, '
              f'at pin configuration(s):\n'
              f'{pins[lowest_max_stress_indices[0], lowest_max_stress_indices[1], :, 0]}')
        print(
            f'At pin(s): {pins[lowest_max_stress_indices[0], lowest_max_stress_indices[1], lowest_max_stress_indices[2], 0]} respectively.\n')


if __name__ == '__main__':
    start_time = time.time()
    main()
    print("--- %s seconds ---" % round((time.time() - start_time), 2))

    # pins_x = pins[:, :, 1]
    # pins_y = pins[:, :, 2]
    # pins_diams = pins[:, :, 3]
    # pins_areas = pins[:, :, 4]
    # pins_x_centr = pins[:, :, 5]
    # pins_y_centr = pins[:, :, 6]
    # pins_to_centr = pins[:, :, 7]
    # pins_ecc_shear = pins[:, :, 8]
    # pins_ecc_x = pins[:, :, 9]
    # pins_ecc_y = pins[:, :, 10]
    # pins_total_shear = pins[:, :, 11]
