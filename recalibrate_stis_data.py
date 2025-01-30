import stistools
import glob
import os
import subprocess

from astropy.io import fits
import glob
import matplotlib
import warnings

def rootname(filename):
    return filename.split("/")[-1].split("_")[0]

def delete_files(del_filetypes, file_loc):
    command_args = ["rm"]
    for filetype in del_filetypes:
        del_files = glob.glob(f"{file_loc}*{filetype}")
        command_args.extend(file for file in del_files)
    subprocess.run(command_args)

def run_x1d(prod_type = "drj", out_prod_type = "sx1"):
    infiles = glob.glob(f"{data_path}/{target_name}*{prod_type}.fits") #defringing/{target_name}*{prod_type}.fits")
    os.chdir(f"{data_path}/") #/defringing/")

    for file in infiles:
        infile = file.split("/")[-1]
        x1d_outfile = infile.replace(f"{prod_type}", f"{prod_type}_{out_prod_type}")
        rootname = file.split("/")[-1].split("_")[0]
        
    delete_files([f"{prod_type}_x1d.fits"], file_loc=f"{data_path}/{target_name}") #defringing/{target_name}")
    stistools.x1d.x1d(infile, output=x1d_outfile, verbose=True, trailer=f"{rootname}.trl") # .trl acts like nohup
    print(f"File written:    {x1d_outfile}")

    # Copy new x1d/sx1 files to datapath for extinction measure
    if x1d_save_path != None:
        command_args = ["cp", f"{x1d_outfile}", f"{x1d_save_path}{rootname}_{out_prod_type}_new.fits"]
        subprocess.run(command_args)
        print(f"1D spectra fits file copied to:   {x1d_save_path}{rootname}_{out_prod_type}_new.fits")


def defringe():
    warnings.filterwarnings("ignore", category=UserWarning)
    matplotlib.rcParams['image.origin'] = 'lower'
    matplotlib.rcParams['image.aspect'] = 'auto'
    matplotlib.rcParams['image.cmap'] = 'plasma'
    matplotlib.rcParams['image.interpolation'] = 'none'
    matplotlib.rcParams['figure.figsize'] = [15, 5]

    current_directory = f"{data_path}/" # TODO: os.getcwd(), f"{data_path}/defringing/

    sci_infile = f"{current_directory}{target_name}" #f"{data_path}/defringing/{target_name}"
    sci_outfile = f"{current_directory}{target_name}" #f"{data_path}/defringing/{target_name}"

    # TODO: 
    flat_name = "oewfr2070" #fits.getheader(f"{sci_infile}_raw.fits",0)['FRNGFLAT'].lower()
    flat_infile = f"{current_directory}{flat_name}" #"{data_path}/defringing/{"oewfr2070"}"
    flat_outfile = f"{current_directory}{flat_name}" #f"{data_path}/defringing/{"oewfr2070"}"


    step = 0 # options: 0, 1, 2, 3, 4, all

    if step == 0 or step == "all":
        #Confirm that the flat file is indeed the associated fringe flat for odvkl3050
        print("Associated Fringe Flat: "+fits.getheader(f"{sci_infile}_raw.fits",0)['FRNGFLAT'])
        print("Observing Mode: "+fits.getheader(f"{sci_infile}_raw.fits",0)['OPT_ELEM'])
        print(flat_name)

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
    delete_files(del_filetypes, file_loc=f"{current_directory}{target_name}")
#    delete_files(del_filetypes, file_loc=f"{current_directory}{flat_name}")

    # 2. Prepare the Science File for the Defringing Correction (Optional)
    #capture the long calstis output
    stistools.defringe.prepspec(f"{sci_infile}_raw.fits")

    prod_type = "crj"
#    if step == 3 or step == "all":
    # 3. Match Fringes in the Fringe Flat Field and the Science Spectra
    # choose the correct science product type based on the mode
    #if mode == "G750L":
    #    prod_type = "crj"
    #elif mode == "G750M":
    #    prod_type = "sx2"

    del_filetypes = ["_frr.fits"]
    delete_files(del_filetypes, file_loc=f"{current_directory}{flat_name}")
        
    stistools.defringe.mkfringeflat(f"{sci_outfile}_{prod_type}.fits", f"{flat_infile}_nsp.fits",
                                f"{flat_outfile}_frr.fits", 
                                beg_shift=-1.0, end_shift=1.0, shift_step=0.02,
                                beg_scale=0.5, end_scale=1.5, scale_step=0.05
                                )

    stistools.defringe.defringe(f"{sci_outfile}_{prod_type}.fits", f"{flat_outfile}_frr.fits", overwrite=True)



# TODO: turn the following into arguments
loc = "Users/cgunasekera"
data_dir = "STIS_Data/HighLowRv_Orig"
data_path = f"/{loc}/AGK+81D266" #/extstar_data/DAT_files/{data_dir}/"
target_name = "oewfr2060" #"ocmv13020"
x1d_save_path = None # options: data_path, None # if left as None, a copy of the x1d data product will not be added elsewhere. 

#case_do = "x1d"

if __name__ == "__main__":
    # Run the following in terminal before starting
    #export CRDS_PATH="$HOME/crds_cache"
    #export CRDS_SERVER_URL="https://hst-crds.stsci.edu"
    #export oref="${CRDS_PATH}/hst/oref/"
    #conda activate stenv

    try: 
        defringe()
        run_x1d()
    except:
        print("Whoops! Need to add path variable for reference files. Run the following in the terminal, and retry.\n")
        print(" conda activate stenv\n export CRDS_PATH=\"$HOME/crds_cache\" \n export CRDS_SERVER_URL=\"https://hst-crds.stsci.edu\" \n export oref=\"${CRDS_PATH}/hst/oref/\"")