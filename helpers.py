"""
Contains helper functions for various tasks
"""

from datetime import timedelta
import re


def convert_time_string_to_integer(time_string):
    """
    Helper function for converting formatted time strings to a single integer
    """
    time_list = re.split("[:.]", time_string)
    time_int = int(time_list[0])*60 + int(time_list[1])
    return time_int

def convert_timedelta_to_clock_time_string(td):
    """
    Helper function for converting timedelta objects to strings that represent the players' remaining time
    """
    # Split timedelta string
    time_list = re.split("[:.]", str(td))
    time_string = ""
    # Adding hours if necessary
    if int(time_list[0]) > 0:
        time_string += time_list[0] + ":"
    # Adding minutes and seconds
    time_string += time_list[1] + ":" + time_list[2]
    # Under 10 sec we increase the resolution
    if td < timedelta(seconds=10):
        time_string += "."
        if len(time_list) >= 4:
            time_string += time_list[3][0]
        else:
            time_string += "0"
    return time_string
