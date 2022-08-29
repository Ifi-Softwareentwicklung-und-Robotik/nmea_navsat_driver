# Created by Lucas Neuber
# This is for you, Köter :P

import socket;
import sys;

import rclpy;

from libnmea_navsat_driver.driver import Ros2NMEADriver;

def main(args=None):
    rclpy.init(args=args)
    driver = Ros2NMEADriver()

    try:
        gnss_host = driver.declare_parameter('host', '192.168.131.22').value
        gnss_port = driver.declare_parameter('port', 9001).value
        buffer_size = driver.declare_parameter('buffer_size', 4096).value
    except KeyError as e:
        driver.get_logger().err("Parameter %s not found" % e)
        sys.exit(1)

    frame_id = driver.get_frame_id()

    driver.get_logger().info("Using gnss sensor with ip {} and port {}".format(gnss_host, gnss_port))

    # Connection-loop: connect and keep receiving. If receiving fails, reconnect
    # Connect to the gnss sensor using tcp
    while rclpy.ok():
        try:
            # Create socket and connect to the gnss sensor
            gnss_socket = socket.create_connection((gnss_host, gnss_port))
        except socket.error as exc:
            driver.get_logger().error("Caught exception socket.error when setting up socket: %s" % exc)
            sys.exit(1)

        # recv-loop: When we're connected, keep receiving stuff until that fails
        partial = ""
        while rclpy.ok():
            try:
                partial += gnss_socket.recv(buffer_size).decode("ascii")

                # strip the data
                lines = partial.splitlines(keepends=True)

                full_lines, last_line = lines[:-1], lines[-1]

                for data in full_lines:
                    try:
                        data = data.replace('\r', '') # Absoluter Pfusch, aber
                        data = data.replace('\n', '') # funktioniert halt :D
                        if driver.add_sentence(data, frame_id):
                            driver.get_logger().info("Received sentence: %s" % data)
                        else:
                            driver.get_logger().warn("Error with sentence: %s" % data)
                    except ValueError as e:
                        driver.get_logger().warn(
                            "Value error, likely due to missing fields in the NMEA message. "
                            "Error was: %s. Please report this issue to me. " % e)
                
                if last_line.endswith("\n"):
                    try:
                        last_line = last_line.replace('\r', '') # Absoluter Pfusch, aber
                        last_line = last_line.replace('\n', '') # funktioniert halt :D
                        if driver.add_sentence(last_line, frame_id):
                            driver.get_logger().info("Received sentence: %s" % last_line)
                        else:
                            driver.get_logger().warn("Error with sentence: %s" % last_line)
                    except ValueError as e:
                        driver.get_logger().warn(
                            "Value error, likely due to missing fields in the NMEA message. "
                            "Error was: %s. Please report this issue to me. " % e)
                    partial = ""
                else:
                    # reset our partial data to this part line
                    partial = last_line


            except socket.error as exc:
                driver.get_logger().error("Caught exception socket.error when receiving: %s" % exc)
                gnss_socket.close()
                break


        gnss_socket.close()
