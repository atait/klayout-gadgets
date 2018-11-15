''' Access the linkers from the command line
'''
import argparse
from lygadgets.salt_linker import link_any
from lygadgets import __version__


parser = argparse.ArgumentParser(description="lygadgets linkers between klayout and system namespaces")
parser.add_argument('sourcepackage', type=str,
                    help='the package to link. Can be a salt directory or a python directory, or the name of an installed python package')
parser.add_argument('-c', '--copy', action='store_true',
                    help='hard copy instead of symbolic linking')
parser.add_argument('-f', '--force', action='store_true',
                    help='overwrite anything present at the destination with the same name')
parser.add_argument('-v', '--version', action='version', version=f'%(prog)s v{__version__}')


def cm_link_any():
    args = parser.parse_args()
    the_links = link_any(args.sourcepackage, overwrite=args.force, hard_copy=args.copy)
    if the_links[0] is None:
        print('No link made. Destination already has a non-symlink item present.')
        print('Use -f if you would like to overwrite')
    else:
        print('Successfully created a {}'.format('hard copy' if args.copy else 'symbolic link'))
        print('From:', the_links[0])
        print('To:  ', the_links[1])

