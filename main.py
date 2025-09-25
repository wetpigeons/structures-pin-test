import itertools
import random
import math

def pinInfo(selection, diameter):
    # (0,0) aligns with left most hole for load & lowest test hole
    # sign convention : up + ccw are positive, down and cw are negative
    # current pinhole grid: 5 rows x 3 columns, half inch spacing between each row and column
    # bottom left hole @ (1.5, 0) -- top right @ (2.5, 2)
    pins = {}
    for i in range(len(selection)):
        pinX = (((selection[i] - 1) % 3) * 0.5) + 1.5
        pinY = ((selection[i] - 1) // 3) * 0.5
        pinArea = math.pi * (diameter[i] ** 2) / 4
        pins[f'Pin {selection[i]}']= {'xPos': pinX, 'yPos': pinY, 'diameter': diameter[i], 'pinArea': pinArea}
    return pins


def centroidAndTorque(pins, load, loadX):
    totalNumX = 0
    totalNumY = 0
    totalArea = 0
    for pin in pins:
        totalArea += pins[pin]['pinArea']   # summation A
        totalNumX += pins[pin]['xPos'] * pins[pin]['pinArea']  # summation x*A
        totalNumY += pins[pin]['yPos'] * pins[pin]['pinArea']  # summation y*A
    centroid = ((totalNumX / totalArea), (totalNumY / totalArea))
    loadOffset = loadX - centroid[0]
    torque = loadOffset * load
    return centroid, torque, loadOffset, totalArea


def distFromCentroid(pins, centroid):
    for pin in pins:
        pins[pin]['xCompDistance'] = pins[pin]['xPos'] - centroid[0]
        pins[pin]['yCompDistance'] = pins[pin]['yPos'] - centroid[1]
        dist = math.sqrt((pins[pin]['xCompDistance'] ** 2) + (pins[pin]['yCompDistance'] ** 2))
        pins[pin]['distance'] = dist


def findShearEccentric(pins, torque):
    for pin in pins:
        tempSum = 0
        if pins[pin]['distance'] != 0:
            for pin2 in pins:
                tempSum += (pins[pin2]['distance'] ** 2) * pins[pin2]['pinArea']
            pins[pin]['shearEccentric'] = -torque / tempSum * (pins[pin]['distance']*pins[pin]['pinArea'])
        else:
            pins[pin]['shearEccentric'] = 0


def shearDirection(pins, torque):
    for pin in pins:
        if pins[pin]['shearEccentric'] != 0:
            if torque < 0:
                tempRotate = (-pins[pin]['yCompDistance'], pins[pin]['xCompDistance']) #(x,y) --> (-y, x) 90 ccw
            else:
                tempRotate = (pins[pin]['yCompDistance'], -pins[pin]['xCompDistance']) #(x,y) --> (y, -x) 90 cw
            magnitude = math.sqrt(tempRotate[0] ** 2 + tempRotate[1] ** 2)
            unitVector = (tempRotate[0] / magnitude, tempRotate[1] / magnitude)
            pins[pin]['shearVector'] = (unitVector[0] * pins[pin]['shearEccentric'], unitVector[1] *
                                                                            pins[pin]['shearEccentric'])
        else:
            pins[pin]['shearVector'] = (0, 0)

def totalShearStress(pins, pinsTested, load, doubleShear, allSame, totalArea):
    maxShear = 0
    minShear = 2147483647
    maxShearPin = ''
    minShearPin = ''
    for pin in pins:
        if allSame:
            pins[pin]['totalVector'] = (pins[pin]['shearVector'][0], pins[pin]['shearVector'][1] - load / pinsTested)
        else:
            pins[pin]['totalVector'] = (pins[pin]['shearVector'][0], pins[pin]['shearVector'][1] - load * (pins[pin]['pinArea'] / totalArea))
        pins[pin]['totalShearForce'] = math.sqrt(pins[pin]['totalVector'][0] ** 2 + pins[pin]['totalVector'][1] ** 2)
        if doubleShear:
            pins[pin]['totalShearStress'] = pins[pin]['totalShearForce'] / (2 * pins[pin]['pinArea'])
        else:
            pins[pin]['totalShearStress'] = pins[pin]['totalShearForce'] / pins[pin]['pinArea']

        if pins[pin]['totalShearStress'] > maxShear:
            maxShear = pins[pin]['totalShearStress']
            maxShearPin = pin
        if pins[pin]['totalShearStress'] < minShear:
            minShear = pins[pin]['totalShearStress']
            minShearPin = pin
    return maxShear, maxShearPin, minShear, minShearPin


def display(pins, maxShear, maxShearPin, minShear, minShearPin, load, loadOffset, pinsTested, doubleShear, allSame):
    print(f'{pinsTested} pins, {load} lb load, offset {round(loadOffset, 3)} in. from the centroid of the pins.')
    print(f'Pins are in a {"double" if doubleShear else "single"} shear configuration with {"all the same diameters" if allSame else "varying diameters"}.')
    for pin in pins:
        print(pin + ":")
        for i in pins[pin]:
            if type(pins[pin][i]) == tuple:
                print("\t" + str(i) + ": " + "<", end="")
                for j in range(len(pins[pin][i])):
                    if j != 0:
                        print(", ", end="")
                    print(str(round(pins[pin][i][j], 3)), end="")
                print(">")
            else:
                print("\t" + str(i) + ": " + str(round(pins[pin][i], 3)))
        print()
    print(f"Max Shear Stress: {round(maxShear, 3)} psi, at {maxShearPin}")
    print(f"Min Shear Stress: {round(minShear, 3)} psi, at {minShearPin}\n")

def pinTest(load, loadX, pinsTested, doubleShear, pinsSelection, pinDiameters):
    pins = pinInfo(pinsSelection, pinDiameters)

    if pinDiameters.count(pinDiameters[0]) == len(pinDiameters):
        allSame = True
    else:
        allSame = False

    centroid, torque, loadOffset, totalArea = centroidAndTorque(pins, load, loadX)
    distFromCentroid(pins, centroid)
    findShearEccentric(pins, torque)
    shearDirection(pins, torque)
    maxShear, maxShearPin, minShear, minShearPin = totalShearStress(pins, pinsTested, load, doubleShear, allSame, totalArea)
    display(pins, maxShear, maxShearPin, minShear, minShearPin, load, loadOffset, pinsTested, doubleShear, allSame)   #console output
    return maxShear, maxShearPin, minShear, minShearPin, loadOffset

def bigPinTest(load, loadX, pinsTested, doubleShear, pinCombinations, pinDiameters):
    overallMaxShear = 0
    overallMaxShearPin = ''
    overallMaxShearPinConfig = []
    greatestMinShear = 0
    greatestMinShearPin = ''
    greatestMinShearPinConfig = []

    if pinDiameters.count(pinDiameters[0]) == len(pinDiameters):
        allSame = True
    else:
        allSame = False

    f = open("output.txt", "w")
    for i in pinCombinations:
        maxShear, maxShearPin, minShear, minShearPin, loadOffset = pinTest(load, loadX, pinsTested, doubleShear, i, pinDiameters)
        if i == pinCombinations[0]:
            f.write(
                '--------------------------------------------------------------------------------------------------------------------\n')
            f.write(f'{pinsTested} pins, {load} lb load, offset {round(loadOffset, 3)} in. from the centroid of the pins.\n')
            f.write(
            f'Pins are in a {"double" if doubleShear else "single"} shear configuration with {f"all the same diameters ({pinDiameters[0]} in.)" if allSame else "varying diameters"}.\n')
            f.write(
                '--------------------------------------------------------------------------------------------------------------------\n\n')
        f.write(f'Pin Configuration: {i}\n')
        f.write(f"\tMax Shear Stress: {round(maxShear, 3)} psi, at {maxShearPin}\n")
        f.write(f"\tMin Shear Stress: {round(minShear, 3)} psi, at {minShearPin}\n\n")
        if maxShear > overallMaxShear:
            overallMaxShear = maxShear
            overallMaxShearPin = maxShearPin
            overallMaxShearPinConfig = i
        if minShear > greatestMinShear:
            greatestMinShear = minShear
            greatestMinShearPin = minShearPin
            greatestMinShearPinConfig = i
    f.write(
        '--------------------------------------------------------------------------------------------------------------------\n')
    f.write(
        f'Maximum Shear Stress: {round(overallMaxShear, 3)} psi at {overallMaxShearPin} in the {pinsTested} pin configuration: {overallMaxShearPinConfig}\n')
    f.write(
        f'Greatest Minimum Shear Stress: {round(greatestMinShear, 3)} psi at {greatestMinShearPin} in the {pinsTested} pin configuration: {greatestMinShearPinConfig}\n')
    f.write(
        '--------------------------------------------------------------------------------------------------------------------')
    f.close()


def main():
    load = 1  # unit load (lbs)
    loadX = 0  # load position (1st hole)
    totalPins = 15  # possible number of pins
    pinsTested = 4
    doubleShear = True
    pinCombinations = list(itertools.combinations(range(1, totalPins + 1), pinsTested))
    pinDiameters = [0.1875, 0.1875, 0.1875, 0.1875]  # inches (default)

    # bigPinTest(load, loadX, pinsTested, doubleShear, pinCombinations, pinDiameters)

    # pinsSelection = pinCombinations[random.randint(0,len(pinCombinations)-1)]     # pick a random combination
    pinsSelection = [4, 6, 10, 12]       # set a desired pin config
    pinTest(load, loadX, pinsTested, doubleShear, pinsSelection, pinDiameters)  # individual pin test


if __name__ == '__main__':
    main()

