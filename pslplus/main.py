from models import *
import sys

if sys.argv[1] == "vqa":
    vqamodel.run(sys.argv[2:])
elif sys.argv[1] == "pslqa":
    pslqamodel.run(sys.argv)
elif sys.argv[1] == "generic":
    pslgeneric.run(sys.argv[2:])