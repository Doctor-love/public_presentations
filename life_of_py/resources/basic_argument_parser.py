#!/usr/bin/env python3
from argparse import ArgumentParser

argument_parser = ArgumentParser(
    description = "Utility to calculate caffeine consumption",
    epilog = "Drink responsibly!")

argument_parser.add_argument(
    "-c", "--cups", type = int, required = True,
    help = "Number of cups consumed during the day")

argument_parser.add_argument(
    "-v", "--verbose", action = "store_true",
    help = "Enable detailed calculation logs")

arguments = argument_parser.parse_args()
