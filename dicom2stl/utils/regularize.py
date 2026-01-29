#! /usr/bin/env python

"""Regularize (resample) a volume to have cubic voxels and identity orientation.

This module resamples medical image volumes so that:
1. All voxels are cubic (same spacing in X, Y, Z directions)
2. The orientation matrix is identity (aligned with world axes)
3. The volume is properly bounded to contain all original data
"""

import sys
from typing import List, Tuple
import SimpleITK as sitk


def regularize(img: sitk.Image, maxdim: int = -1, verbose: bool = False) -> sitk.Image:
    """Resample a volume to have cubic voxels and identity orientation matrix.
    
    This function resamples the input image so that:
    - Voxels are cubic (isotropic spacing)
    - Orientation matrix is identity
    - All original data is preserved within the bounding box
    
    Args:
        img: Input SimpleITK image to regularize
        maxdim: Maximum dimension for the output volume. If -1, uses max dimension of input.
        verbose: If True, print detailed processing information
        
    Returns:
        Regularized SimpleITK image with cubic voxels and identity orientation
    """
    dims = img.GetSize()

    if verbose:
        print("Input dimensions:", dims)
        print("Input origin:", img.GetOrigin())
        print("Input direction:", img.GetDirection())
        print("Input spacing:", img.GetSpacing())

    # Define corners of the volume in voxel (index) space
    vcorners = [
        [0, 0, 0],
        [dims[0], 0, 0],
        [0, dims[1], 0],
        [dims[0], dims[1], 0],
        [0, 0, dims[2]],
        [dims[0], 0, dims[2]],
        [0, dims[1], dims[2]],
        [dims[0], dims[1], dims[2]],
    ]

    # Transform corners from voxel space to world (physical) space
    wcorners = []
    mins = [1e32, 1e32, 1e32]
    maxes = [-1e32, -1e32, -1e32]
    for corner in vcorners:
        wcorners.append(img.TransformContinuousIndexToPhysicalPoint(corner))

    # Compute the axis-aligned bounding box in world space
    for corner in wcorners:
        for i in range(3):
            mins[i] = min(mins[i], corner[i])
            maxes[i] = max(maxes[i], corner[i])

    if verbose:
        print("Bounding box min:", mins)
        print("Bounding box max:", maxes)

    # Determine maximum dimension for output volume
    if maxdim < 0:
        maxdim = max(dims)

    # Calculate isotropic voxel spacing based on largest bounding box dimension
    maxrange = max(maxes[i] - mins[i] for i in range(3))
    newspacing = maxrange / maxdim
    if verbose:
        print("New isotropic spacing:", newspacing)

    # Calculate dimensions for the new regularized volume
    newdims = [int((maxes[i] - mins[i]) / newspacing + 0.5) for i in range(3)]
    if verbose:
        print("New dimensions:", newdims)

    # Resample to create regularized volume with cubic voxels and identity orientation
    identity_direction = [1, 0, 0, 0, 1, 0, 0, 0, 1]
    isotropic_spacing = [newspacing, newspacing, newspacing]
    
    newimg = sitk.Resample(
        img,
        newdims,
        sitk.Transform(),
        sitk.sitkLinear,
        mins,
        isotropic_spacing,
        identity_direction,
        img.GetPixelID(),
    )

    return newimg


def main() -> None:
    """Main entry point for the regularize command-line tool."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Regularize a volume to have cubic voxels and identity orientation."
    )
    parser.add_argument(
        "input",
        nargs="?",
        help="Input volume file (if omitted, runs test mode)"
    )
    parser.add_argument(
        "output",
        nargs="?",
        help="Output volume file"
    )
    parser.add_argument(
        "-d", "--dim",
        type=int,
        default=128,
        metavar="N",
        help="Maximum dimension for output volume (default: 128)"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    
    args = parser.parse_args()
    
    # Test mode - no input file provided
    if args.input is None:
        print("Running in test mode...")
        input_img = sitk.GaussianSource(
            sitk.sitkUInt8,
            size=[256, 256, 74],
            sigma=[20, 20, 5],
            mean=[128, 128, 37],
            scale=255,
        )
        input_img.SetSpacing([0.4, 0.4, 2.0])
        input_img.SetOrigin([25.0, 50.0, 75.0])
        a = 0.70710678
        input_img.SetDirection([a, a, 0, a, -a, 0, 0, 0, 1])
        sitk.WriteImage(input_img, "testimg.nrrd")
        print("Wrote test input: testimg.nrrd")

        outimg = regularize(input_img, 200, verbose=True)
        sitk.WriteImage(outimg, "testoutimg.nrrd")
        print("\nWrote test output: testoutimg.nrrd")
        print("\nOutput image info:")
        print(outimg)
    else:
        # Normal mode - process input file
        if args.output is None:
            parser.error("Output file is required when input file is provided")
        
        print(f"Reading: {args.input}")
        input_img = sitk.ReadImage(args.input)
        
        out_img = regularize(input_img, args.dim, args.verbose)
        
        print(f"Writing: {args.output}")
        sitk.WriteImage(out_img, args.output)
        print("Done!")
