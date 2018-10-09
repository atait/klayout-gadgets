''' Access the linkers from the command line
'''
import argparse
from lygadgets.salt_linker import link_any
from lygadgets import __version__


parser = argparse.ArgumentParser(description="lygadgets linkers between klayout and system namespaces")
parser.add_argument('sourcepackage', type=str,
                    help='the package to link. Can be a salt directory or a python directory, or the name of an installed python package')
parser.add_argument('-f', '--force', action='store_true',
                    help='(NOT functional in v0.0.8) overwrite anything present at the destination with the same name')
parser.add_argument('-v', '--version', action='version', version=f'%(prog)s v{__version__}')


def cm_link_any():
    args = parser.parse_args()
    the_links = link_any(args.sourcepackage)
    if the_links[0] is None:
        print('No link made. Destination already has something there.')
    else:
        print('Successfully created a symbolic link')
        print('From:', the_links[0])
        print('To:  ', the_links[1])

