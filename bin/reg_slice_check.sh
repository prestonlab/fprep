#!/bin/bash
#
# Create an image with slices to check the quality of registration of two images.

if [[ $# -lt 4 ]]; then
    echo "Create an image with slices to check the quality of registration of two images."
    echo
    echo "Usage: reg_slice_check.sh image1 image2 pngdir pngout"
    exit 1
fi

DIST=".35 .45 .55 .65"
AXIS="x y z"

N=0
FILES=""
for a in $AXIS; do
    for d in $DIST; do
        N=$((N+1))
        slicer "$1" "$2" -s 2 "-$a" "$d" "$3/tempslice$N.png"
        FILES="$FILES $3/tempslice$N.png"
    done
done

C=""
for f in $FILES; do
    C="$C + $f"
done

C=$(echo "$C" | cut -c 3-)
pngappend $C "$3/$4"
rm $FILES
