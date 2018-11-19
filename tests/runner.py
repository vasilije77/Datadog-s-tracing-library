"""
A custom test runner for ddtrace integrations.

Patch tests are separated out and run using a cleantest runner. All other tests
are loaded and run with normal unittest machinery.
"""
import argparse
import unittest
import sys
import os

from tests.cleantest import CleanTestLoader


parser = argparse.ArgumentParser(description='Run tests for a ddtrace integration.')
parser.add_argument(
    'dir',
    metavar='directory',
    type=str,
    help='directory to search for tests related to an integration',
)


class IntegrationTestLoader(unittest.TestLoader):
    def _match_path(self, path, full_path, pattern):
        return 'test_patch' not in path and 'test_patch' not in full_path


def main():
    args = parser.parse_args()
    cwd = os.getcwd()
    sys.path.pop(0)
    sys.path.insert(0, cwd)
    test_dir = os.path.join(cwd, args.dir)
    modprefix = args.dir.replace(os.path.sep, '.')

    loader = IntegrationTestLoader()
    patch_loader = CleanTestLoader(modprefix)

    suite = unittest.TestSuite([
            loader.discover(test_dir, top_level_dir=cwd),
            patch_loader.discover(test_dir, pattern='test_patch.py'),
    ])
    result = unittest.TextTestRunner().run(suite)
    sys.exit(not result.wasSuccessful())


if __name__ == '__main__':
    main()
