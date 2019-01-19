import sys
import os

from src.config_handler import ConfigHandler
from src.argument_handler import ArgumentHandler
from src.file_handler import FileHandler
from src.network_handler import NetworkHandler
from src.os_handler import OSHandler
from src.print_handler import PrintHandler

from time import sleep

def main():

    c = ConfigHandler()
    p = PrintHandler(c)
    #a = ArgumentHandler(c, sys.argv[1])
    #a.load_inote(sys.argv[1])
    #f = FileHandler(c, a, sys.argv[1])
    #n = NetworkHandler(c, f)
    #o = OSHandler(c, a, f)

    izumi = p.get_logger()
    izumi.info("Hello World")

    #o.create_temp_replica_fs()

    #sleep(20)
    #o.upload()
    #o.cleanup()

    print("-------")


if __name__ == "__main__":
    main()
