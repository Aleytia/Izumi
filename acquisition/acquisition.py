import sys
import os

from src.config_handler import ConfigHandler
from src.argument_handler import ArgumentHandler
from src.file_handler import FileHandler
from src.network_handler import NetworkHandler
from src.os_handler import OSHandler

def main():

    c = ConfigHandler()
    a = ArgumentHandler(c, sys.argv[1])
    #a.load_inote(sys.argv[1])
    f = FileHandler(c, a, sys.argv[1])
    n = NetworkHandler(c, f)
    o = OSHandler(c, a, f)

    o.create_temp_replica_fs()
    o.upload()
    o.cleanup()

    print("-------")


if __name__ == "__main__":
    main()
