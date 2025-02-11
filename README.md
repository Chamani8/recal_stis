# recal_stis
Recalibrate STIS data. 

This is a python wrapper for the stistools pipeline.
The script defringes and produces the 1D spectra 
using the raw observations. 

## Setup

1. Install stistools, see [https://stistools.readthedocs.io/](https://stistools.readthedocs.io/en/latest/gettingstarted.html)

2. The following files are needed to run the script:
`*_raw.fits`
`*_nsp.fits`
`*_wav.fits`
`*_frr.fits`
`*_crj.fits`
`*_asn.fits`

3. The script will also require the associate reference 
files.

## Run

1. Enable the stis environment

`>> conda activate stisenv`

2. Add the path to the reference files to your path

`>> export CRDS_PATH="$HOME/crds_cache"`
`>> export CRDS_SERVER_URL="https://hst-crds.stsci.edu"`
`>> export oref="${CRDS_PATH}/references/hst/oref/"`

3. Run the script in the repository with the raw image 
files (e.g. `ofaj01040_raw.fits`) from command line:

`>> python3 <path/to/script>/recalibrate_stis_data.py ofaj01040`

By default the script will use the association file, 
`ofaj01040_asn.fits`, to find which file to use as the flat-field 
image. A different flat-field file can be used by calling:

`>> python3 <path/to/script>/recalibrate_stis_data.py ofaj01040 --flat_infile="ofaj01050_raw.fits"`
