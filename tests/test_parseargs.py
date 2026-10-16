"""Tests for combining command-line filter options."""

import unittest

from dicom2stl.utils import parseargs


class TestFilterOptions(unittest.TestCase):
    """Filter flags preserve the user's command-line ordering."""

    def test_anisotropic_after_other_filters(self):
        for options, expected in [
            (["--anisotropic"], ["anisotropic"]),
            (["--disable", "shrink", "--anisotropic"],
             ["noshrink", "anisotropic"]),
            (["--largest", "--anisotropic"], ["largest", "anisotropic"]),
            (["--enable", "median", "--anisotropic"],
             ["median", "anisotropic"]),
            (["--disable", "anisotropic", "--anisotropic"],
             ["noanisotropic", "anisotropic"]),
        ]:
            with self.subTest(options=options):
                args = parseargs.createParser().parse_args(
                    options + ["volume.nrrd"]
                )
                self.assertEqual(args.filters, expected)
