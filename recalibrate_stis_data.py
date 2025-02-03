import stistools
import glob
import os
import subprocess

from astropy.io import fits
import glob
import matplotlib
import warnings
import argparse


def rootname(filename):
    return filename.split("/")[-1].split("_")[0]

def delete_files(del_filetypes, file_loc):
    command_args = ["rm"]
    for filetype in del_filetypes:
        del_files = glob.glob(f"{file_loc}*{filetype}")
        command_args.extend(file for file in del_files)
    subprocess.run(command_args)

def run_x1d(sci_infile, x1d_save_path, x1d_infile_type, x1d_outfile_type):
    infiles = glob.glob(f"{sci_infile}*{x1d_infile_type}.fits")

    for file in infiles:
        infile = file.split("/")[-1]
        x1d_outfile = infile.replace(f"{x1d_infile_type}", f"{x1d_infile_type}_{x1d_outfile_type}")
        rootname = file.split("/")[-1].split("_")[0]
        
    delete_files([f"{x1d_infile_type}_x1d.fits"], file_loc=sci_infile)
    stistools.x1d.x1d(infile, output=x1d_outfile, verbose=True, trailer=f"{rootname}.trl") # .trl acts like nohup
    print(f"File written:    {x1d_outfile}")

    # Copy new x1d/sx1 files to datapath for extinction measure
    if x1d_save_path != None:
        command_args = ["cp", f"{x1d_outfile}", f"{x1d_save_path}{rootname}_{x1d_outfile_type}.fits"]
        subprocess.run(command_args)
        print(f"1D spectra fits file copied to:   {x1d_save_path}{rootname}_{x1d_outfile_type}.fits")


def defringe(sci_infile, flat_infile):
    warnings.filterwarnings("ignore", category=UserWarning)

    flat_outfile = flat_infile
    sci_outfile = sci_infile

    step = 0 # options: 0, 1, 2, 3, 4, all

    if step == 0 or step == "all":
        #Confirm that the flat file is indeed the associated fringe flat for odvkl3050
        print("Associated Fringe Flat: "+fits.getheader(f"{sci_infile}_raw.fits",0)['FRNGFLAT'])
        print("Observing Mode: "+fits.getheader(f"{sci_infile}_raw.fits",0)['OPT_ELEM'])

#    if step == 1 or step == "all":
    # 1. Normalize the Fringe Flat
    stistools.defringe.normspflat(f"{flat_infile}_raw.fits",
                              f"{flat_infile}_nsp.fits", do_cal=True,
                              wavecal=f"{sci_infile}_raw.fits")

    # Flatten the blue end of the flat-field image [ONLY FOR G750L]
    with fits.open(f"{flat_infile}_nsp.fits", mode='update') as hdulist:
        hdulist[1].data[:,:250] = 1

#    if step == 2 or step == "all":
    del_filetypes = ["_crj.fits", "_flt.fits", "_sx1.fits", "_tmp.fits", "_sx2.fits"]
    delete_files(del_filetypes, file_loc=sci_infile)

    # 2. Prepare the Science File for the Defringing Correction (Optional)
    #capture the long calstis output
    stistools.defringe.prepspec(f"{sci_infile}_raw.fits")

    mode = fits.getheader(f"{sci_infile}_raw.fits",0)['OPT_ELEM']
#    if step == 3 or step == "all":
    # 3. Match Fringes in the Fringe Flat Field and the Science Spectra
    # choose the correct science product type based on the mode
    if mode == "G750L":
        prod_type = "crj"
    elif mode == "G750M":
        prod_type = "sx2"

    del_filetypes = ["_frr.fits"]
    delete_files(del_filetypes, file_loc=flat_infile)
        
    stistools.defringe.mkfringeflat(f"{sci_outfile}_{prod_type}.fits", f"{flat_infile}_nsp.fits",
                                f"{flat_outfile}_frr.fits", 
                                beg_shift=-1.0, end_shift=1.0, shift_step=0.02,
                                beg_scale=0.5, end_scale=1.5, scale_step=0.05
                                )

    stistools.defringe.defringe(f"{sci_outfile}_{prod_type}.fits", f"{flat_outfile}_frr.fits", overwrite=True)

def main(sci_infile, flat_infile, x1d_infile_type, x1d_outfile_type, x1d_save_path):
    if flat_infile != None: flat_infile =  fits.getheader(f"{sci_infile}_raw.fits",0)['FRNGFLAT'].lower()

    try:
        defringe(sci_infile, flat_infile)
        run_x1d(sci_infile, x1d_save_path, x1d_infile_type, x1d_outfile_type)
    except:
        print("Whoops! Need to add path variable for reference files. Run the following in the terminal, and retry.\n")
        print(" conda activate stenv\n export CRDS_PATH=\"$HOME/crds_cache\" \n export CRDS_SERVER_URL=\"https://hst-crds.stsci.edu\" \n export oref=\"${CRDS_PATH}/hst/oref/\"")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Defringe and create 1D spectra for STIS.")
    parser.add_argument('sci_infile', type=str, help="Science input filename.")
    parser.add_argument('--flat_infile', type=str, default=None, help="Flat input filename.")
    parser.add_argument('--x1d_save_path', type=str, default=None, help="Path other than current working directory, to save x1d file.")
    parser.add_argument('--x1d_infile_type', type=str, default="drj", help="Path other than current working directory, to save x1d file.")
    parser.add_argument('--x1d_outfile_type', type=str, default="sx1", help="Path other than current working directory, to save x1d file.")

    args = parser.parse_args()

    main(args.sci_infile, args.flat_infile, args.x1d_infile_type, args.x1d_outfile_type, args.x1d_save_path)