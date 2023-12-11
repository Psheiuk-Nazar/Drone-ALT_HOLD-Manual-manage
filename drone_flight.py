import math
import time
from dronekit import connect, VehicleMode, LocationGlobalRelative

import argparse

parser = argparse.ArgumentParser(description='Commands vehicle using vehicle.simple_goto.')
parser.add_argument('--connect',
                    help="Vehicle connection target string. If not specified, SITL automatically started and used.")
args = parser.parse_args()

connection_string = args.connect
sitl = None

if not connection_string:
    import dronekit_sitl

    sitl = dronekit_sitl.start_default()
    connection_string = sitl.connection_string()

print('Connecting to vehicle on: %s' % connection_string)
vehicle = connect(connection_string, wait_ready=True)


def arm_and_takeoff(aTargetAltitude):
    print("Basic pre-arm checks")

    while not vehicle.is_armable:
        print(" Waiting for vehicle to initialise...")
        time.sleep(1)

    print("Arming motors")

    vehicle.armed = True

    while not vehicle.armed:
        print(" Waiting for arming...")
        time.sleep(1)
        vehicle.armed = True

    print("Taking off!")
    while True:
        if vehicle.location.global_relative_frame.alt < aTargetAltitude * 0.9:
            vehicle.channels.overrides['3'] = 2200
        elif vehicle.location.global_relative_frame.alt > aTargetAltitude * 0.9:
            vehicle.channels.overrides['3'] = 1750
        print(" Altitude: ", vehicle.location.global_relative_frame.alt)
        if vehicle.location.global_relative_frame.alt >= aTargetAltitude * 0.995:
            print("Reached target altitude")
            vehicle.channels.overrides['3'] = 1500
            break
        time.sleep(1)


def get_distance_metres(aLocation1, aLocation2):
    dlat = aLocation2.lat - aLocation1.lat
    dlong = aLocation2.lon - aLocation1.lon
    return math.sqrt((dlat * dlat) + (dlong * dlong)) * 1.113195e5


def get_bearing(aLocation1, aLocation2):
    off_x = aLocation2.lon - aLocation1.lon
    off_y = aLocation2.lat - aLocation1.lat
    bearing = 90.00 + math.atan2(-off_y, off_x) * 57.2957795
    if bearing < 0:
        bearing += 360.00
    return bearing


def way_to_point(wpl):
    vehicle.mode = VehicleMode("ALT_HOLD")
    vehicle.channels.overrides['2'] = 1000
    distance_new = int(get_distance_metres(vehicle.location.global_frame, wpl))
    distance_old = distance_new + 1
    while True:
        if distance_new > distance_old:
            vehicle.channels.overrides['2'] = 1500
            time.sleep(2)
            yaw_needs = get_bearing(vehicle.location.global_frame, wpl)
            condition_yaw(yaw_needs)
            return way_to_point(wpl)
        if distance_new > 300:
            time.sleep(5)
            distance_old = distance_new
            distance_new = int(get_distance_metres(vehicle.location.global_frame, wpl))
            print(f"Distance to destination: {distance_new}")
        elif 300 >= distance_new > 50:
            vehicle.channels.overrides['2'] = 1200
            time.sleep(2)
            distance_old = distance_new
            distance_new = int(get_distance_metres(vehicle.location.global_frame, wpl))
            print(f"Distance to destination: {distance_new}")
        elif 50 >= distance_new >= 3:
            vehicle.channels.overrides['2'] = 1400
            time.sleep(1)
            distance_old = distance_new
            distance_new = int(get_distance_metres(vehicle.location.global_frame, wpl))
            print(f"Distance to destination: {distance_new}")
        else:
            print("Drone at the destination")
            vehicle.channels.overrides['2'] = 1500
            break


def condition_yaw(yaw_need):
    while int(vehicle.heading) != int(yaw_need):
        if vehicle.heading < yaw_need:
            vehicle.channels.overrides['4'] = 1550
        else:
            vehicle.channels.overrides['4'] = 1450
        time.sleep(0.5)

    vehicle.channels.overrides['4'] = 1500
    print(vehicle.heading)


if __name__ == "__main__":
    while not vehicle.mode == "ALT_HOLD":
        print(" Waiting for ALT_HOLD mode...")
        time.sleep(1)
    arm_and_takeoff(100)

    point_A = vehicle.location.global_frame
    point_B = LocationGlobalRelative(50.443326, 30.448078)
    yaw = get_bearing(point_A, point_B)
    condition_yaw(yaw)
    way_to_point(point_B)
    condition_yaw(350)
    time.sleep(5)
    print("Mission to Complete --> I'm pretty a BOY")
    print(
        f"Vehicle Yaw: {vehicle.heading}, Vehicle position {vehicle.location.global_frame}, Vehicle mode: {vehicle.mode}")
    vehicle.close()

if sitl:
    sitl.stop()
