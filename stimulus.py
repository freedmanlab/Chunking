import numpy as np
import matplotlib.pyplot as plt
from parameters import *


class Stimulus:

    def __init__(self):

        # generate tuning functions
        self.motion_tuning, self.fix_tuning, self.rule_tuning, self.response_tuning = self.create_tuning_functions()


    def generate_trial(self, analysis = False, num_fixed = 0,var_delay=False,var_resp_delay=False,var_num_pulses=False,test_mode_pulse=False, pulse=0, test_mode_delay=False):
        if var_delay or var_resp_delay or var_num_pulses:
            return self.generate_var_chunking_trial(par['num_pulses'], analysis, num_fixed, var_delay, var_resp_delay, var_num_pulses, test_mode_pulse, pulse, test_mode_delay)
        else:
            return self.generate_chunking_trial(par['num_pulses'], analysis, num_fixed)


    def generate_chunking_trial(self, num_pulses, analysis, num_fixed):
        """
        Generate trials to investigate chunking
        """

        # rule signal can appear at the end of delay1_time
        trial_length = par['num_time_steps']

        # end of trial epochs
        eodead = par['dead_time']//par['dt']
        eof = (par['dead_time']+par['fix_time'])//par['dt']    
        eos = [(par['dead_time']+par['fix_time']+ n*par['delay_time'] + (n+1)*par['sample_time'])//par['dt'] for n in range(num_pulses)]
        eods = [(par['dead_time']+par['fix_time']+(n+1)*(par['sample_time']+par['delay_time']))//par['dt'] for n in range(num_pulses-1)]
        eods.append(eos[-1])
        eolongd = (par['dead_time']+par['fix_time'] + num_pulses * par['sample_time'] + (num_pulses-1)*par['delay_time'] + par['long_delay_time'])//par['dt']
        eor = [(par['dead_time']+par['fix_time'] + num_pulses * par['sample_time'] + (num_pulses-1)*par['delay_time'] + par['long_delay_time'] + \
            n*par['delay_time'] + (n+1)*par['resp_cue_time'])//par['dt'] for n in range(num_pulses)]
        eodr = [(par['dead_time']+par['fix_time'] + num_pulses * par['sample_time'] + (num_pulses-1)*par['delay_time'] + par['long_delay_time'] + \
            (n+1)*(par['resp_cue_time']+par['delay_time']))//par['dt'] for n in range(num_pulses-1)]
        eodr.append(eor[-1])
        # end of neuron indices
        emt = par['num_motion_tuned']
        eft = par['num_fix_tuned']+par['num_motion_tuned']
        ert = par['num_fix_tuned']+par['num_motion_tuned'] + par['num_resp_cue_tuned']
        if par['order_cue']:
            eot = par['num_fix_tuned']+par['num_motion_tuned'] + par['num_resp_cue_tuned'] + par['num_order_cue_tuned']

        trial_info = {'desired_output'  :  np.zeros((par['n_output'], trial_length, par['batch_train_size']),dtype=np.float32),
                      'train_mask'      :  np.ones((trial_length, par['batch_train_size']),dtype=np.float32),
                      'rule'            :  np.zeros((par['batch_train_size']),dtype=np.int8),
                      'sample'          :  np.zeros((par['batch_train_size'], par['num_pulses']),dtype=np.int8),
                      'neural_input'    :  np.random.normal(par['input_mean'], par['noise_in'], size=(par['n_input'], trial_length, par['batch_train_size'])),
                      'timeline'        :  [eodead, eof]}

        trial_info['timeline'].append(eos[0])
        for i in range(1,num_pulses):
            trial_info['timeline'].append(eods[i-1])
            trial_info['timeline'].append(eos[i])
        trial_info['timeline'].append(eolongd)
        trial_info['timeline'].append(eor[0])
        for i in range(1,num_pulses):
            trial_info['timeline'].append(eodr[i-1])
            trial_info['timeline'].append(eor[i])

        # set to mask equal to zero during the dead time
        trial_info['train_mask'][:eodead, :] = 0
        trial_info['train_mask'][eolongd:eolongd+par['mask_duration']//par['dt'], :] = 0
        for i in range(1, par['num_pulses']):
            trial_info['train_mask'][eodr[i-1]:eodr[i-1]+par['mask_duration']//par['dt'], :] = 0
        # If the DMS and DMS rotate are being performed together,
        # or if I need to make the test more challenging, this will eliminate easry test directions
        # If so, reduce set of test stimuli so that a single strategy can't be used
        #limit_test_directions = par['trial_type']=='DMS+DMRS'

        for t in range(par['batch_train_size']):

            """
            Generate trial paramaters
            """
            if not analysis:
                sample_dirs = [np.random.randint(par['num_motion_dirs']) for i in range(num_pulses)]
            else:
                sample_dirs = [0]*num_fixed + [np.random.randint(par['num_motion_dirs']) for i in range(num_pulses-num_fixed)]

            rule = np.random.randint(par['num_rules'])

            """
            Calculate neural input based on sample, tests, fixation, rule, and probe
            """
            # SAMPLE stimulus
            trial_info['neural_input'][:emt, eof:eos[0], t] += np.reshape(self.motion_tuning[:,sample_dirs[0]],(-1,1))
            for i in range(1,num_pulses):
                trial_info['neural_input'][:emt, eods[i-1]:eos[i], t] += np.reshape(self.motion_tuning[:,sample_dirs[i]],(-1,1))

            # FIXATION cue
            if par['num_fix_tuned'] > 0:
                trial_info['neural_input'][emt:eft, eodead:eolongd, t] += np.reshape(self.fix_tuning[:,0],(-1,1))
                for i in range(num_pulses):
                    trial_info['neural_input'][emt:eft, eor[i]:eodr[i], t] += np.reshape(self.fix_tuning[:,0],(-1,1))

            # RESPONSE CUE
            trial_info['neural_input'][eft:ert, eolongd:eor[0], t] += np.reshape(self.response_tuning[:,0],(-1,1))
            for i in range(1, num_pulses):
                trial_info['neural_input'][eft:ert, eodr[i-1]:eor[i], t] += np.reshape(self.response_tuning[:,0],(-1,1))

            # ORDER CUE
            if par['order_cue']:
                trial_info['neural_input'][ert, eolongd:eor[0], t] += par['tuning_height']
                trial_info['neural_input'][ert, eof:eos[0], t] += par['tuning_height']
                for i in range(1,par['num_pulses']):
                    trial_info['neural_input'][ert+i, eodr[i-1]:eor[i], t] += par['tuning_height']
                    trial_info['neural_input'][ert+i, eods[i-1]:eos[i], t] += par['tuning_height']

            """
            Determine the desired network output response
            """
            trial_info['desired_output'][0, eodead:eolongd, t] = 1
            for i in range(num_pulses):
                trial_info['desired_output'][0, eor[i]:eodr[i], t] = 1

            trial_info['desired_output'][sample_dirs[0]+1, eolongd:eor[0], t] = 1
            for i in range(1, num_pulses):
                trial_info['desired_output'][sample_dirs[i]+1, eodr[i-1]:eor[i], t] = 1

            """
            Append trial info
            """
            trial_info['sample'][t,:] = sample_dirs
            trial_info['rule'][t] = rule

        return trial_info

    def generate_var_chunking_trial(self, num_pulses, analysis, num_fixed, var_delay=False, var_resp_delay=False, var_num_pulses=False, test_mode_pulse=False, pulse=0, test_mode_delay=False):
        """
        Generate trials to investigate chunking
        """

        # rule signal can appear at the end of delay1_time
        trial_length = par['num_time_steps']

        # end of neuron indices
        emt = par['num_motion_tuned']
        eft = par['num_fix_tuned']+par['num_motion_tuned']
        ert = par['num_fix_tuned']+par['num_motion_tuned'] + par['num_resp_cue_tuned']
        if par['order_cue']:
            eot = par['num_fix_tuned']+par['num_motion_tuned'] + par['num_resp_cue_tuned'] + par['num_order_cue_tuned']

        trial_info = {'desired_output'  :  np.zeros((par['n_output'], trial_length, par['batch_train_size']),dtype=np.float32),
                      'train_mask'      :  np.ones((trial_length, par['batch_train_size']),dtype=np.float32),
                      'rule'            :  np.zeros((par['batch_train_size']),dtype=np.int8),
                      'sample'          :  np.zeros((par['batch_train_size'], par['num_max_pulse']),dtype=np.int32),
                      'neural_input'    :  np.random.normal(par['input_mean'], par['noise_in'], size=(par['n_input'], trial_length, par['batch_train_size'])),
                      'timeline'        :  [0]*par['batch_train_size'],
                      'num_pulses'      :  np.zeros(par['batch_train_size'],dtype=np.int32),
                      'delay'           :  np.zeros((par['batch_train_size'], par['num_max_pulse']),dtype=np.int32),
                      'resp_delay'      :  np.zeros((par['batch_train_size'], par['num_max_pulse']-1),dtype=np.int32)}

        if var_num_pulses:
            if test_mode_pulse:
                trial_info['num_pulses'][:] = pulse
            else:
                trial_info['num_pulses'] = np.random.choice(range(par['num_max_pulse']//2,par['num_max_pulse']+1),size=par['batch_train_size'])
        else:
            trial_info['num_pulses'][:] = par['num_pulses']

        if var_delay:
            if test_mode_delay:
                print('Setting unifom delay time...')
                trial_info['delay'][:,:par['num_max_pulse']-1] = 200
                trial_info['delay'][:,-1] = 500
            else:
                trial_info['delay'][:,:par['num_max_pulse']-1] = np.random.choice([100,200,300],size=(par['batch_train_size'],par['num_max_pulse']-1))
                trial_info['delay'][:, -1] = np.random.choice([500,700], size=par['batch_train_size'])
            trial_info['delay'][:,2] = trial_info['delay'][:,-1]
        else:
            trial_info['delay'][:,:par['num_max_pulse']-1] = par['delay_time']
            trial_info['delay'][:,-1] = par['long_delay_time']

        if var_resp_delay:
            if test_mode_delay:
                print('Setting unifom response delay time...')
                trial_info['resp_delay'][:,:par['num_max_pulse']-1] = 200
            else:
                trial_info['resp_delay'][:,:par['num_max_pulse']-1] = np.random.choice([100,200,300],size=(par['batch_train_size'],par['num_max_pulse']-1))
        else:
            trial_info['resp_delay'][:,:par['num_max_pulse']-1] = par['delay_time']


        # If the DMS and DMS rotate are being performed together,
        # or if I need to make the test more challenging, this will eliminate easry test directions
        # If so, reduce set of test stimuli so that a single strategy can't be used
        #limit_test_directions = par['trial_type']=='DMS+DMRS'

        for t in range(par['batch_train_size']):

            """
            Generate trial paramaters
            """

            num_pulses = trial_info['num_pulses'][t]
            delay = trial_info['delay'][t]
            resp_delay = trial_info['resp_delay'][t]

            # end of trial epochs
            eodead = par['dead_time']//par['dt']
            eof = (par['dead_time']+par['fix_time'])//par['dt']
            eos = [(par['dead_time']+par['fix_time']+ np.sum(delay[:n]) + (n+1)*par['sample_time'])//par['dt'] for n in range(num_pulses)]
            eods = [(par['dead_time']+par['fix_time']+(n+1)*(par['sample_time'])+np.sum(delay[:n+1]))//par['dt'] for n in range(num_pulses-1)]
            eods.append(eos[-1])
            eolongd = (par['dead_time']+par['fix_time'] + num_pulses * par['sample_time'] + np.sum(delay[:num_pulses-1]) + delay[-1])//par['dt']
            eor = [(par['dead_time']+par['fix_time'] + num_pulses * par['sample_time'] + np.sum(delay[:num_pulses-1]) + delay[-1] + \
                np.sum(resp_delay[:n]) + (n+1)*par['resp_cue_time'])//par['dt'] for n in range(num_pulses)]
            eodr = [(par['dead_time']+par['fix_time'] + num_pulses * par['sample_time'] +  np.sum(delay[:num_pulses-1]) + delay[-1] + \
                (n+1)*(par['resp_cue_time'])+np.sum(resp_delay[:n+1]))//par['dt'] for n in range(num_pulses-1)]
            eodr.append(eor[-1])

            # Timeline
            timeline = [eodead,eof]
            timeline.append(eos[0])
            for i in range(1,num_pulses):
                timeline.append(eods[i-1])
                timeline.append(eos[i])
            timeline.append(eolongd)
            timeline.append(eor[0])
            for i in range(1,num_pulses):
                timeline.append(eodr[i-1])
                timeline.append(eor[i])
            trial_info['timeline'][t] = timeline


            # set to mask equal to zero during the dead time
            trial_info['train_mask'][:eodead, t] = 0
            trial_info['train_mask'][eolongd:eolongd+par['mask_duration']//par['dt'], t] = 0
            for i in range(1, num_pulses):
                trial_info['train_mask'][eodr[i-1]:eodr[i-1]+par['mask_duration']//par['dt'], t] = 0
            trial_info['train_mask'][eor[-1]:, t] = 0

            if not analysis:
                sample_dirs = [np.random.randint(par['num_motion_dirs']) for i in range(num_pulses)]
            else:
                sample_dirs = [0]*num_fixed + [np.random.randint(par['num_motion_dirs']) for i in range(num_pulses-num_fixed)]

            rule = np.random.randint(par['num_rules'])

            """
            Calculate neural input based on sample, tests, fixation, rule, and probe
            """
            # SAMPLE stimulus
            trial_info['neural_input'][:emt, eof:eos[0], t] += np.reshape(self.motion_tuning[:,sample_dirs[0]],(-1,1))
            for i in range(1,num_pulses):
                trial_info['neural_input'][:emt, eods[i-1]:eos[i], t] += np.reshape(self.motion_tuning[:,sample_dirs[i]],(-1,1))

            # FIXATION cue
            if par['num_fix_tuned'] > 0:
                trial_info['neural_input'][emt:eft, eodead:eolongd, t] += np.reshape(self.fix_tuning[:,0],(-1,1))
                for i in range(num_pulses):
                    trial_info['neural_input'][emt:eft, eor[i]:eodr[i], t] += np.reshape(self.fix_tuning[:,0],(-1,1))

            # RESPONSE CUE
            trial_info['neural_input'][eft:ert, eolongd:eor[0], t] += np.reshape(self.response_tuning[:,0],(-1,1))
            for i in range(1, num_pulses):
                trial_info['neural_input'][eft:ert, eodr[i-1]:eor[i], t] += np.reshape(self.response_tuning[:,0],(-1,1))

            # ORDER CUE
            if par['order_cue']:
                trial_info['neural_input'][ert, eolongd:eor[0], t] += par['tuning_height']
                trial_info['neural_input'][ert, eof:eos[0], t] += par['tuning_height']
                for i in range(1,num_pulses):
                    trial_info['neural_input'][ert+i, eodr[i-1]:eor[i], t] += par['tuning_height']
                    trial_info['neural_input'][ert+i, eods[i-1]:eos[i], t] += par['tuning_height']

            """
            Determine the desired network output response
            """
            trial_info['desired_output'][0, eodead:eolongd, t] = 1
            for i in range(num_pulses):
                trial_info['desired_output'][0, eor[i]:eodr[i], t] = 1

            trial_info['desired_output'][sample_dirs[0]+1, eolongd:eor[0], t] = 1
            for i in range(1, num_pulses):
                trial_info['desired_output'][sample_dirs[i]+1, eodr[i-1]:eor[i], t] = 1

            """
            Append trial info
            """
            trial_info['sample'][t,:num_pulses] = sample_dirs
            trial_info['rule'][t] = rule

        if par['check_stim']:
            for i in range(5):
                plt.figure()
                plt.title("num_pulses: "+str(trial_info['num_pulses'][i])+"\nvar_delay: "+str(list(trial_info['delay'][i,:trial_info['num_pulses'][i]-1])+[trial_info['delay'][i,-1]])+"\nresp_delay: "+str(trial_info['resp_delay'][i,:trial_info['num_pulses'][i]]))
                plt.imshow(trial_info['neural_input'][:,:,i],aspect='auto')
                plt.colorbar()
                plt.show()
                plt.close()
                plt.figure()
                plt.plot(trial_info['train_mask'][:,i])
                plt.title("num_pulses: "+str(trial_info['num_pulses'][i])+"\nvar_delay: "+str(list(trial_info['delay'][i,:trial_info['num_pulses'][i]-1])+[trial_info['delay'][i,-1]])+"\nresp_delay: "+str(trial_info['resp_delay'][i,:trial_info['num_pulses'][i]]))
                plt.show()
                plt.close()
                plt.figure()
                plt.imshow(trial_info['desired_output'][:,:,i],aspect='auto')
                plt.title("num_pulses: "+str(trial_info['num_pulses'][i])+"\nvar_delay: "+str(list(trial_info['delay'][i,:trial_info['num_pulses'][i]-1])+[trial_info['delay'][i,-1]])+"\nresp_delay: "+str(trial_info['resp_delay'][i,:trial_info['num_pulses'][i]]))
                plt.colorbar()
                plt.show()
                plt.close()

        return trial_info

    def create_tuning_functions(self):

        """
        Generate tuning functions for the Postle task
        """
        motion_tuning = np.zeros((par['num_motion_tuned'], par['num_receptive_fields'], par['num_motion_dirs']))
        fix_tuning = np.zeros((par['num_fix_tuned'], par['num_receptive_fields']))
        rule_tuning = np.zeros((par['num_rule_tuned'], par['num_rules']))
        response_tuning = np.zeros((par['num_resp_cue_tuned'], par['num_receptive_fields']))

        # generate list of prefered directions
        # dividing neurons by 2 since two equal groups representing two modalities
        pref_dirs = np.float32(np.arange(0,360,360/(par['num_motion_tuned']//par['num_receptive_fields'])))

        # generate list of possible stimulus directions
        stim_dirs = np.float32(np.arange(0,360,360/par['num_motion_dirs']))

        for n in range(par['num_motion_tuned']//par['num_receptive_fields']):
            for i in range(len(stim_dirs)):
                for r in range(par['num_receptive_fields']):
                    d = np.cos((stim_dirs[i] - pref_dirs[n])/180*np.pi)
                    n_ind = n+r*par['num_motion_tuned']//par['num_receptive_fields']
                    motion_tuning[n_ind,r,i] = par['tuning_height']*np.exp(par['kappa']*d)/np.exp(par['kappa'])

        for n in range(par['num_fix_tuned']):
            for i in range(par['num_receptive_fields']):
                if n%par['num_receptive_fields'] == i:
                    fix_tuning[n,i] = par['tuning_height']

        for n in range(par['num_resp_cue_tuned']):
            for i in range(par['num_receptive_fields']):
                if n%par['num_receptive_fields'] == i:
                    response_tuning[n,i] = par['tuning_height']

        for n in range(par['num_rule_tuned']):
            for i in range(par['num_rules']):
                if n%par['num_rules'] == i:
                    rule_tuning[n,i] = par['tuning_height']


        return np.squeeze(motion_tuning), fix_tuning, rule_tuning, response_tuning


    def plot_neural_input(self, trial_info):

        print(trial_info['desired_output'][ :, 0, :].T)
        f = plt.figure(figsize=(8,4))
        ax = f.add_subplot(1, 1, 1)
        t = np.arange(0,400+500+2000,par['dt'])
        t -= 900
        t0,t1,t2,t3 = np.where(t==-500), np.where(t==0),np.where(t==500),np.where(t==1500)
        #im = ax.imshow(trial_info['neural_input'][:,0,:].T, aspect='auto', interpolation='none')
        im = ax.imshow(trial_info['neural_input'][:,:,0], aspect='auto', interpolation='none')
        #plt.imshow(trial_info['desired_output'][:, :, 0], aspect='auto')
        ax.set_xticks([t0[0], t1[0], t2[0], t3[0]])
        ax.set_xticklabels([-500,0,500,1500])
        ax.set_yticks([0, 9, 18, 27])
        ax.set_yticklabels([0,90,180,270])
        f.colorbar(im,orientation='vertical')
        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)
        ax.set_ylabel('Motion direction')
        ax.set_xlabel('Time relative to sample onset (ms)')
        ax.set_title('Motion input')
        plt.show()
        plt.savefig('stimulus.pdf', format='pdf')
