#!/usr/bin/python3
# -*- coding: utf-8 -*-
import re
import sys
from ibm_vpc_img_inst.main import builder

def entry():
    sys.argv[0] = re.sub(r'(-script\.pyw|\.exe)?$', '', sys.argv[0])
    sys.exit(builder())






