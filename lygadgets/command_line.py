''' Access the linkers from the command line
'''
import argparse
from lygadgets.salt_linker import link_any, unlink_any
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


unlink_parser = argparse.ArgumentParser(description='lygadgets unlink anything')
unlink_parser.add_argument('sourcepackage', type=str,
                    help='the package to unlink. Can be name of a package or technology')
unlink_parser.add_argument('-f', '--force', action='store_true',
                    help='delete non-symlink directories. Be careful')
unlink_parser.add_argument('-v', '--version', action='version', version=f'%(prog)s v{__version__}')

def cm_unlink_any():
    args = unlink_parser.parse_args()
    unlink_any(args.sourcepackage, force=args.force)
