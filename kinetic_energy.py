import time
import datetime
import numpy as n
import h5py
import matplotlib.pyplot as plt
import os

# estimate mean kinetic energy as a function of time of day and height

# our internal modules
import mmaria_read as mr
import cfi_dac as cfi
import cfi_config as c
import mean_wind_est as mw

from mpi4py import MPI
comm=MPI.COMM_WORLD
size=comm.Get_size()
rank=comm.Get_rank()


def avg_ke_acfs(md,
                dcos_thresh=0.8,
                tods=n.arange(48)*0.5, # hours
                dt=0.5,
                ds_h=25.0,
                heights=n.arange(75,120), # km
                years=[2018,2019,2020],
                months=[5,6,7],
                name="summer_small_ke"):

    if rank == 0:
        os.system("rm mpi/%s/ke_res*.h5"%(name))
        os.system("mkdir -p mpi/%s"%(name))
    comm.Barrier()

    # how many heights and time of days
    n_height=len(heights)
    n_t = len(tods)

    pars=[]
    for year in years:
        for month in months:
            for week in range(4):
                pars.append([year,month,week*7.0+1])
            
    n_pars=len(pars)
    print("n_runs %d"%(n_pars))    
    
    for pi in range(rank,n_pars,size):
        year=pars[pi][0]
        month=pars[pi][1]
        day=pars[pi][2]
        d0=datetime.date(year,month,int(day))
        t0=time.mktime(d0.timetuple())

        acfs=n.zeros([6,n_t,n_height])
        errs=n.zeros([6,n_t,n_height])
        d=md.read_data(t0=t0-3600,t1=t0+7*24*3600+3600.0)
        meas=cfi.get_meas(meas_file=d,
                          mean_rem=False,
                          plot_dops=False,
                          dcos_thresh=dcos_thresh,
                          data='mmaria')
        
        for ti,tod in enumerate(tods):
            for hi,h0 in enumerate(heights):
                n_meas=len(d["t"])
                print("n_meteors %d"%(n_meas))
                if n_meas > 100:
                    print("tod %f h %f"%(tod,h0))

                    acf, err, itaus, ixs, iys, izs, is_h=cfi.cfi(meas,
                                                                 h0=h0,
                                                                 dh=2,
                                                                 ds_z=1.0,
                                                                 ds_h=ds_h,
                                                                 dtau=dt*3600.0,
                                                                 horizontal_dist=True,
                                                                 hour_of_day=tod,
                                                                 dhour_of_day=dt)
                    acfs[:,ti,hi]=acf
                    errs[:,ti,hi]=err
  #      plt.pcolormesh(tods,heights,n.transpose(acfs[0,:,:]+acfs[1,:,:]),vmin=0,vmax=10000.0)
 #       plt.colorbar()
#        plt.show()
        ho=h5py.File("mpi/%s/ke_res-%06d.h5"%(name,rank),"w")
        ho["acfs"]=acfs
        ho["errs"]=errs
        ho["tods"]=tods
        ho["heights"]=heights
        ho["ds_h"]=ds_h
        ho.close()

md=mr.mmaria_data(c.data_directory)#for many files in a directory
b=md.get_bounds()

def summer_small():
    """ small scale kinetic energy summer months """
    avg_ke_acfs(md,
                tods=n.arange(24), # hours
                dt=1.0,
                ds_h=50.0,
                heights=n.arange(70,120), # km
                years=[2018,2019],
                months=[5,6,7],
                name="summer_small_ke")

def winter_small():
    """ small scale kinetic energy winter months """

    avg_ke_acfs(md,
                tods=n.arange(24), # hours
                dt=1.0,
                ds_h=50.0,
                heights=n.arange(70,120), # km
                years=[2018,2019,2020],
                months=[11,12,1],
                name="winter_small_ke")

def monthly_small():
    """ mohtly kinetic energy small scale """
    for mi in range(12):
        avg_ke_acfs(md,
                    tods=n.arange(24), # hours
                    dt=1.0,
                    ds_h=50.0,
                    heights=n.arange(70,120), # km
                    years=[2018,2019,2020],
                    months=[mi+1],
                    name="%02d_small_ke"%(mi))

def monthly_large():
    """ mohtly kinetic energy large scale """
    for mi in range(12):
        avg_ke_acfs(md,
                    tods=n.arange(24), # hours
                    dt=1.0,
                    ds_h=500.0,
                    heights=n.arange(70,120), # km
                    years=[2018,2019,2020],
                    months=[mi+1],
                    name="%02d_large_ke"%(mi))

monthly_large()
