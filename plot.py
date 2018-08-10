import pickle
import matplotlib.pyplot as plt
import matplotlib as mpl
from parameters import *

def plot_pev_cross_time(x, num_pulses, cue, pev_type):
    fig, axes = plt.subplots(nrows=num_pulses, ncols=1)
    i = 0
    for ax in axes.flat:
        im = ax.imshow(x[pev_type][:,i,:],aspect='auto')
        i += 1
    cax,kw = mpl.colorbar.make_axes([ax for ax in axes.flat])
    plt.colorbar(im, cax=cax, **kw)
    plt.savefig("./savedir/"+pev_type+"_cross_time_"+str(num_pulses)+"_pulses_"+cue+".png")

def plot_pev_after_stim(x, num_pulses, cue, pev_type,time_lapse):
    # fig, axes = plt.subplots(nrows=1, ncols=num_pulses)
    # i = 0
    # for ax in axes.flat:
    #     #im = ax.imshow(x[pev_type][:,:,x['timeline'][2*i+1]+time_lapse],aspect='auto')
    #     eolongd = (par['dead_time']+par['fix_time'] + num_pulses * par['sample_time'] + (num_pulses-1)*par['delay_time'] + par['long_delay_time'])//par['dt']
    #     im = ax.imshow(x[pev_type][:,:,eolongd-time_lapse],aspect='auto')
    #     i += 1
    # cax,kw = mpl.colorbar.make_axes([ax for ax in axes.flat])
    # plt.colorbar(im, cax=cax, **kw)
    eolongd = (par['dead_time']+par['fix_time'] + num_pulses * par['sample_time'] + (num_pulses-1)*par['delay_time'] + par['long_delay_time'])//par['dt']
    plt.imshow(x[pev_type][:,:,eolongd-time_lapse],aspect='auto')
    plt.savefig("./savedir/"+pev_type+"_after_stim_"+str(num_pulses)+"_pulses_"+cue+".png")
    plt.close()
    m = np.array(x[pev_type][:,:,eolongd-time_lapse])
    plt.hist(np.sum((m>0.1),axis=1), bins=range(9))
    plt.xticks(range(9))
    #plt.xlim(xmin=0, xmax=8)
    plt.savefig("./savedir/"+pev_type+"_selectivity_"+str(num_pulses)+"_pulses_"+cue+".png")
    plt.close()

def shufffle_pev(x, num_pulses, cue, pev_type, acc_type, time_lapse):
    test_onset = [np.unique(np.array(x['timeline']))[-2*p-2] for p in range(num_pulses)][::-1]
    nrows = num_pulses/2 if num_pulses%2==0 else num_pulses
    ncols = 2 if num_pulses%2==0 else 1

    fig, axes = plt.subplots(nrows=nrows, ncols=ncols)
    i = 0
    for ax in axes.flat:
        ax.scatter(x[pev_type][:,i,test_onset[i]-1], np.mean(x[acc_type][i,:],axis=1), aspect='auto')
        i += 1
    plt.savefig("./savedir/"+pev_type+"_shuffle_"+str(num_pulses)+"_pulses_"+cue+".png")

num_pulses = [8]
cue_list = ['cue_on']
pev_type = ['synaptic_pev']
acc_type = ['accuracy_syn_shuffled']

for num_pulses in num_pulses:
    for cue in cue_list:
        for type in pev_type:
            for acc in acc_type:
                x = pickle.load(open('./savedir/analysis_chunking_'+str(num_pulses)+"_"+cue+".pkl", 'rb'))
                #plot_pev_cross_time(x, num_pulses, cue, type)
                plot_pev_after_stim(x, num_pulses, cue, type, 10)
                shufffle_pev(x, num_pulses, cue, type, acc_type, 10)
