import sys
import os

from robot.libdoc import libdoc

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ROOT, 'src'))

if __name__ == '__main__':
    ipath = os.path.join(ROOT, 'src', 'PysphereLibrary')
    opath_html = os.path.join(ROOT, 'doc', 'PysphereLibrary.html')
    opath_xml = os.path.join(ROOT, 'doc', 'PysphereLibrary.xml')
    try:
        libdoc(ipath, opath_html)
        libdoc(ipath, opath_xml)
    except:
        print __doc__