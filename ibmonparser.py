# ============================================================
# Project : Server Rack Monitoring & Alert System
# File    : ibmnonparser.py
# Author  : Renjith Kumar
# Created : 
# Purpose : Main program
#
# Description:
#
#
# ============================================================
import sys

import ibmrack_batchalert
import ibmrack_rack_alert
import ibmrack_base_parser
import ibmrack_deep_parser

def print_help():

    print("\nUsage ---------------------------------:")

    print("  ibmrackparser rackalert")
    print("  ibmrackparser batchalert")
    print("  ibmrackparser simplescan")
    print("  ibmrackparser deepscan")

    print("\nCommands and Purpose:")
    print("  rackalert   -> Monitor specific racks and write into alert.log file")
    print("  batchalert  -> Scan all racks in the pod and write into alert.log file")
    print("  simplescan  -> Scans the home page, writes Zora's status into Excel file")
    print("  deepscan    -> Opens each rack's detailed page, writes status into Excel file")
    print("\n------------------------------------------:")
    print(" Designed & developed by: Renjith Kumar.")
    print(" Release date: 05/15/2026.")


def main():
    # NO ARGUMENT
    if len(sys.argv) < 2:
        print_help()
        return

    mode = sys.argv[1].lower()

    if mode == "help" or mode == "h" or mode == "about":
        print_help()

    elif mode == "rackalert":
        ibmrack_rack_alert.main()

    elif  mode == "batchalert":
        ibmrack_batchalert.main()

    elif mode == "simplescan":
        ibmrack_base_parser.main()

    elif mode == "deepscan":
            ibmrack_deep_parser.main()
    else:
        print_help()


if __name__ == "__main__":
    main()
    print ("Execution of main thread completed.")