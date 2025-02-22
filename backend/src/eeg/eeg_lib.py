import re
from typing import Type
import mne
import os
import numpy as np
from django.conf import settings
from eegflow.settings.base import MEDIA_TEMP, MEDIA_STORED, MEDIA_PROC_TEMP_OUTPUT_PATH


def convert_to_db(x, data_type='power'):
    '''
    For Power and Energy, use 10*log10(x). For amplitude, use 20*log10(x) ;)
    '''
    if data_type=='power' or data_type=='energy':
        return 10*np.log10(np.maximum(x, np.finfo(float).tiny))
    else: # amplitude -> db
        return 20*np.log10(np.maximum(x, np.finfo(float).tiny))

    

def set_instance_reference(instance, type_of_set_ref='monopolar', **kwargs): 

    if type_of_set_ref=='monopolar':
        if isinstance(instance,mne.BaseEpochs):
            instance.load_data()
            instance_eeg = instance.copy().pick_types(eeg=True)
        else:
            instance_eeg = instance.copy().pick_types(eeg=True)
            instance_eeg.load_data()

        channel=kwargs["channel"] # channel name or 'average'
        try:
            instance_referenced=instance_eeg.set_eeg_reference(
                ref_channels=channel,
                projection=False
            )
        except Exception as ex:
            raise ex

    elif type_of_set_ref=='bipolar':
        anode=kwargs["anode"]
        cathode=kwargs["cathode"]
        ch_name=kwargs["ch_name"]
        drop_refs=kwargs["drop_refs"]

        if isinstance(instance,mne.BaseEpochs):
            instance.load_data()
            instance_referenced = instance.copy().pick_types(eeg=True)
        else:
            instance_referenced = instance.copy().pick_types(eeg=True)
            instance_referenced.load_data()

        try:
            mne.set_bipolar_reference(
                instance_referenced,
                anode=anode,
                cathode=cathode,
                ch_name=ch_name,
                copy=False,
                drop_refs=drop_refs
            )
        except Exception as ex:
            raise ex

    return instance_referenced


# Instance must be epochs or evoked
def time_frequency(instance, picks=None, type_of_tf='morlet', return_itc=False, **kwargs):
    average = kwargs["average"]
    try:
        if type_of_tf == 'morlet':
            data = mne.time_frequency.tfr_morlet(
                instance,
                picks=picks,
                freqs=kwargs["freqs"],
                n_cycles=kwargs["n_cycles"],
                use_fft=True,
                return_itc=return_itc,
                decim=1,
                n_jobs=1,
                average=average,
            )
        elif type_of_tf == 'multitaper':
            data = mne.time_frequency.tfr_multitaper(
                instance,
                picks=picks,
                freqs=kwargs["freqs"],
                n_cycles=kwargs["n_cycles"],
                time_bandwidth=kwargs["time_bandwidth"],
                use_fft=True,
                return_itc=return_itc,
                decim=1,
                n_jobs=1,
                average=average,
            )

        elif type_of_tf == 'stockwell':
            data = mne.time_frequency.tfr_stockwell(
                instance,
                picks=picks,
                fmin=kwargs["fmin"],
                fmax=kwargs["fmax"],
                n_fft=kwargs["n_fft"],
                width=kwargs["width"],
                return_itc=return_itc,
                decim=1,
                n_jobs=1,
                average=average,
            )
    except Exception as ex:
        raise ex

    return data


# Instance can be epochs or raw
def psd(instance, freq_window, time_window=(None, None), picks=None, type_of_psd='welch', **kwargs):
    try:
        if type_of_psd == 'welch':
            psds, freqs = mne.time_frequency.psd_welch(
                inst=instance,
                tmin=time_window[0], tmax=time_window[1],
                fmin=freq_window[0], fmax=freq_window[1],
                picks=picks,
                n_fft=kwargs["n_fft"],
                n_overlap=kwargs["n_overlap"],
                n_per_seg=kwargs["n_per_seg"],
                average=kwargs["average"],
                window=kwargs["window"],
                verbose=False
            )

        elif type_of_psd == 'multitaper':
            psds, freqs = mne.time_frequency.psd_multitaper(
                inst=instance,
                tmin=time_window[0], tmax=time_window[1],
                fmin=freq_window[0], fmax=freq_window[1],
                picks=picks,
                bandwidth=kwargs["bandwidth"],
                adaptive=kwargs["adaptive"],
                low_bias=kwargs["low_bias"],
                normalization=kwargs["normalization"],
                verbose=False
            )
    except Exception as ex:
        raise ex
    # [psds]=amp**2/Hz
    scaling=1e6
    psds_db = []
    # psd_db=[]
    for psd in psds:
        psds_db.append(map(convert_to_db, psd*scaling*scaling))

    return psds_db, freqs


def get_epochs(media_path, filepath):
    try:
        full_filepath = os.path.join(media_path, filepath)
        epochs = mne.read_epochs(full_filepath)
    except Exception as ex:
        raise ex

    return epochs


def get_raw(media_path, filepath):
    file_extension = filepath.split('.')[1]
    full_filepath = os.path.join(media_path, filepath)
    if file_extension == 'set':  # EEGLAB
        raw = mne.io.read_raw_eeglab(full_filepath)
    elif file_extension == 'fif':  # MNE
        raw = mne.io.read_raw_fif(full_filepath)
    elif file_extension == 'edf':  # European Data Format
        raw = mne.io.read_raw_edf(full_filepath)
    else:
        raise TypeError

    return raw


def save_raw(instance, filename, overwrite=True):
    instance.save(filename, overwrite=overwrite)
    return


def add_events(instance, new_events):
    if new_events is None:
        return instance

    
    if isinstance(instance,mne.BaseEpochs):
        raise TypeError
    else:
        instance_eeg_stim = instance.copy().pick_types(eeg=True, stim=True)
        instance_eeg_stim.load_data()


    if 'stim' in instance_eeg_stim.get_channel_types():
        instance_eeg_stim.add_events(new_events)  # , stim_channel='STI 014')
    else:
        # create new channel for events and add new ones
        info = mne.create_info(['STI 014'], instance_eeg_stim.info['sfreq'], ['stim'])
        stim_data = np.zeros((1, len(instance_eeg_stim.times))) #create empty channel
        stim_raw = mne.io.RawArray(stim_data, info)

        # add new stim channel
        instance_eeg_stim.add_channels([stim_raw], force_update_info=True)
        
        # add events and new events
        events, events_dict = mne.events_from_annotations(instance_eeg_stim)
        instance_eeg_stim.add_events(events)
        instance_eeg_stim.add_events(new_events)
    return instance_eeg_stim


def get_events(instance):
    # TODO: Previamente averiguar cual channel tiene
    try:
        # , stim_channel='STI 014') Si no pongo un canal especifico, busca en distintos canales
        events = mne.find_events(instance)
    except ValueError:
        print("[INFO] the file doesn't have events... trying with annotations...")
        try:
            events, events_dict = mne.events_from_annotations(instance)
        except Exception as ex:
            print("[INFO] the file doesn't have events")
            raise ex

    return events


def notch_filter(instance, notch_freqs=[50.0], channels=None, filter_method='fir', **kwargs):
    
    if isinstance(instance,mne.BaseEpochs):
        instance.load_data()
        instance_eeg = instance.copy().pick_types(eeg=True)
    else:
        instance_eeg = instance.copy().pick_types(eeg=True)
        instance_eeg.load_data()

    try:
        if channels == None:  # Si es None, aplico el filtrado en todos los canales tipo EEG
            channels_idxs = mne.pick_types(instance.info, eeg=True)
        else:
            channels_idxs = mne.pick_channels(
                instance_eeg.info['ch_names'], include=channels,ordered=True)
    except Exception as ex:
        raise ex

    try:
        if filter_method == 'spectrum_fit':
            instance_eeg.apply_function(
                fun=mne.filter.notch_filter,
                picks=channels_idxs,
                dtype=None,
                n_jobs=1,
                channel_wise=True,
                verbose=None,
                Fs=instance_eeg.info["sfreq"],
                freqs=None,
                method=filter_method,
                notch_widths=kwargs["notch_widths"],
                mt_bandwidth=kwargs["mt_bandwidth"],
                p_value=kwargs["p_value"],
            )
        elif filter_method == 'fir':
            instance_eeg.apply_function(
                fun=mne.filter.notch_filter,
                picks=channels_idxs,
                dtype=None,
                n_jobs=1,
                channel_wise=True,
                verbose=None,
                Fs=instance_eeg.info["sfreq"],
                freqs=tuple(notch_freqs),
                method=filter_method,
                notch_widths=kwargs["notch_widths"],
                trans_bandwidth=kwargs["trans_bandwidth"],
                phase=kwargs["phase"],
                fir_window=kwargs["fir_window"],
                fir_design=kwargs["fir_design"],
            )
        else:
            instance_eeg.apply_function(
                fun=mne.filter.notch_filter,
                picks=channels_idxs,
                dtype=None,
                n_jobs=1,
                channel_wise=True,
                verbose=None,
                Fs=instance_eeg.info["sfreq"],
                freqs=tuple(notch_freqs),
                method=filter_method,
                notch_widths=kwargs["notch_widths"],
                iir_params=kwargs["iir_params"]
            )
    except Exception as ex:
        raise ex

    return instance_eeg


def custom_filter(instance, low_freq=None, high_freq=None, channels=None, filter_method='fir', **kwargs):

    if isinstance(instance,mne.BaseEpochs):
        instance.load_data()
        instance_eeg = instance.copy().pick_types(eeg=True)
    else:
        instance_eeg = instance.copy().pick_types(eeg=True)
        instance_eeg.load_data()

    try:
        if channels == None:  # Si es None, aplico el filtrado en todos los canales tipo EEG
            channels_idxs = mne.pick_types(instance.info, eeg=True)
        else:
            channels_idxs = mne.pick_channels(
                instance_eeg.info['ch_names'], include=channels,ordered=True)
    except Exception as ex:
        raise ex
    
    try:
        if filter_method == 'fir':
            instance_filtered = instance_eeg.filter(
                l_freq=low_freq,
                h_freq=high_freq,
                picks=channels_idxs,
                method=filter_method,
                l_trans_bandwidth=kwargs["l_trans_bandwidth"],
                h_trans_bandwidth=kwargs["h_trans_bandwidth"],
                phase=kwargs["phase"],
                fir_window=kwargs["fir_window"],
                fir_design=kwargs["fir_design"],
            )
        else:
            instance_filtered = instance_eeg.filter(
                l_freq=low_freq,
                h_freq=high_freq,
                picks=channels_idxs,
                method=filter_method,
                iir_params=kwargs["iir_params"]
            )
    except Exception as ex:
        raise ex

    return instance_filtered


def peak_finder(instance, channels=None, thresh=None):

    if isinstance(instance,mne.BaseEpochs):
        instance.load_data()
        instance_eeg = instance.copy().pick_types(eeg=True)
    else:
        instance_eeg = instance.copy().pick_types(eeg=True)
        instance_eeg.load_data()

    try:
        if channels == None:  # Si es None, aplico el filtrado en todos los canales tipo EEG
            channels_idxs = mne.pick_types(instance_eeg.info, eeg=True)
        else:
            channels_idxs = mne.pick_channels(
                instance_eeg.info['ch_names'], include=channels,ordered=True)
    except Exception as ex:
        raise ex

    time_series = instance_eeg.get_data(picks=channels_idxs)
    peaks = []
    if isinstance(instance,mne.BaseEpochs):
        peaks_per_epoch=[]
        for epoch in time_series:
            for channel in epoch:
                try:
                    locs, amplitudes = mne.preprocessing.peak_finder(channel, thresh=thresh)
                    peaks.append({"locations": locs, "amplitudes": amplitudes})
                except Exception as ex:
                    raise ex
            
            peaks_per_epoch.append(peaks)
            peaks=[]
        
        peaks=peaks_per_epoch
    else:
        for serie in time_series:
            try:
                locs, amplitudes = mne.preprocessing.peak_finder(serie, thresh=thresh)
                peaks.append({"locations": locs, "amplitudes": amplitudes})
            except Exception as ex:
                raise ex

    return peaks
