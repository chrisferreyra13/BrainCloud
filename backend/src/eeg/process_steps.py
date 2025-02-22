from django.core.files import base
from mne import event
from .eeg_lib import *
from .utils import *
from eegflow.settings.base import MEDIA_TEMP, MEDIA_STORED, MEDIA_PROC_TEMP_OUTPUT_PATH

LOAD_RESTORE_PARAM_NAME = 'id'

def bad_channels(**kwargs):
    input=kwargs["input"]
    params=kwargs["params"]

    #get requested channels to mark as 'bads'
    channels=get_request_channels(params)
    if type(channels)==Response:
        return channels  
    
    ch_names=input.info['ch_names']   # Obtengo los nombres de los canales tipo EEG
    try:
        if set(channels).issubset(set(ch_names)):
            input.info['bads'].extend(channels)  # add a list of channels
        else:
            return Response('An invalid list of channels has been provided.',
                        status=status.HTTP_400_BAD_REQUEST)
    except:
        return Response('An invalid list of channels has been provided.',
                        status=status.HTTP_400_BAD_REQUEST)

    return input

def set_reference(**kwargs):
    input=kwargs["input"]
    params=kwargs["params"]

    #get type of tf
    if 'type' not in params:
        type_of_set_ref='monopolar'
    else:
        type_of_set_ref=params['type']
        if (not type_of_set_ref) or (type_of_set_ref == ''):    # Por defecto uso monopolar
            type_of_set_ref='monopolar'
        else:
            if type_of_set_ref not in ["monopolar","bipolar"]:
                return Response('An invalid type of setting reference method has been provided.',
                    status=status.HTTP_400_BAD_REQUEST)
    
    ch_names=input.info['ch_names']
    if 'ref_channel' not in params:
        ref_channel=None
    else:
        ref_channel=params['ref_channel']
        if (not ref_channel) or (ref_channel == ''):    # Si no envian nada, lo aplico en todos los canales
            ref_channel=None
        else:
            if set(ref_channel).issubset(set(ch_names)):
                return Response('An invalid reference channel has been provided.',
                    status=status.HTTP_400_BAD_REQUEST)

    if 'anode' not in params:
        anode=None
    else:
        anode=params['anode']
        if (not anode) or (anode == ''):    # Si no envian nada, lo aplico en todos los canales
            anode=None
        else:
            if set(anode).issubset(set(ch_names)):
                return Response('An invalid anode has been provided.',
                    status=status.HTTP_400_BAD_REQUEST)
    
    if 'cathode' not in params:
        cathode=None
    else:
        cathode=params['cathode']
        if (not cathode) or (cathode == ''):    # Si no envian nada, lo aplico en todos los canales
            cathode=None
        else:
            if set(cathode).issubset(set(ch_names)):
                return Response('An invalid cathode has been provided.',
                    status=status.HTTP_400_BAD_REQUEST)  
        
    # get if average result for morlet o multitaper (stockwell always average result)
    if 'average' not in params:
        average=False
    else:
        average=params["average"]
        if (not average) or (average == ''):    # Si no envian nada, lo aplico en todos los canales
            average=False
        else:
            if average in ["true","false"]:
                average=True if average=='true' else False
            else:
                return Response('An invalid average value has been provided.',
                    status=status.HTTP_400_BAD_REQUEST)


    if type_of_set_ref=='monopolar':
        if ref_channel is None and average is False:
            # return Response('No reference channel hasn´t been provided.',
            #         status=status.HTTP_400_BAD_REQUEST)
            average=True    # Default 


        if average:
            ref_channel='average'
            ref_params={"channel":ref_channel}
        else:
            ref_params={"channel":[ref_channel]}

    else:
        if anode is None or cathode is None:
            return Response('No reference channel hasn´t been provided.',
                    status=status.HTTP_400_BAD_REQUEST)

        fields=["ch_name","drop_refs"]
        defaults=[None,False]
        ref_params=check_params(params,params_names=fields,params_values=defaults)
        if type(ref_params)==Response: return ref_params
        
        ref_params["anode"]=anode
        ref_params["cathode"]=cathode

    try:
        output=set_instance_reference(
            instance=input,
            type_of_set_ref=type_of_set_ref,
            **ref_params
            )
    except Exception as ex:
        return ex
    

    return output


def epochs(**kwargs):
    input=kwargs["input"]
    params=kwargs["params"]

    if 'tmin' not in params:
        tmin=-0.2
    else:
        tmin=params['tmin']
        if (not tmin) or (tmin == ''):
            tmin=-0.2
        else:
            try:
                tmin=float(tmin)
            except:
                return Response('An invalid min time has been provided.',
                    status=status.HTTP_400_BAD_REQUEST)
    
    if 'tmax' not in params:
        tmax=0.5
    else:
        tmax=params['tmax']
        if (not tmax) or (tmax == ''):
            tmax=0.5
        else:
            try:
                tmax=float(tmax)
            except:
                return Response('An invalid max time has been provided.',
                    status=status.HTTP_400_BAD_REQUEST)


    # get baseline correction
    if 'baseline' not in params:
        baseline = None
    else:
        baseline=params['baseline']
        if (not baseline) or (baseline == []) or (baseline == ''):
            baseline = None
        else:
            if baseline == ',':
                baseline=(None, None) # Apply baseline correction to full time range
            else:
                try:
                    baseline=tuple([float(f) for f in baseline.split(',')])
                except:
                    return Response('An invalid baseline correction range has been provided.',
                        status=status.HTTP_400_BAD_REQUEST)
            
                if baseline[0]>baseline[1]:
                    return Response('An invalid baseline correction range has been provided.',
                        status=status.HTTP_400_BAD_REQUEST)

    # get event ids
    if 'event_id' not in params:
        event_id = None  # default: use all events
    else:
        event_id=params['event_id']
        if (not event_id) or (event_id == []) or (event_id == '') or (event_id == ','):
            event_id=None
        else:
            try:
                event_id=[int(f) for f in event_id.split(',')]
            except:
                return Response('An invalid list of event ids has been provided.',
                    status=status.HTTP_400_BAD_REQUEST)
            

    #get requested channels
    channels=get_request_channels(params)
    if type(channels)==Response:
        return channels  
    
    if channels==None: # Si es None, agarro todos
        channels_idxs=mne.pick_types(input.info,eeg=True) #Retorna los indices internos de raw
        #eeg_info=mne.pick_info(input.info, sel=channels_idxs)
    else:
        ch_names=input.info['ch_names']   # Obtengo los nombres de los canales tipo EEG
        if set(channels).issubset(set(ch_names)):
            channels_idxs=mne.pick_channels(ch_names, include=channels,ordered=True) #Retorna los indices internos de raw
        else:
            return Response('An invalid list of channels has been provided.',
                        status=status.HTTP_400_BAD_REQUEST)

    try:
        events=get_events(input)
    except Exception as ex:
        return Response('Invalid file extension',
                    status=status.HTTP_406_NOT_ACCEPTABLE)
    
    if event_id is not None:
        event_id=[id for id in event_id if id in events[:,2]]
        if len(event_id)==0:
            event_id=None #uso esto para que no explote
            print("[INFO]: event ids don't match with true event ids")
            #usar esto dps
            #return Response('An invalid list of event ids has been provided.',
            #            status=status.HTTP_400_BAD_REQUEST

    try:
        # build epochs instance for time-frequency plot
        epochs = mne.Epochs(
            raw=input, 
            events=events,
            event_id=event_id, 
            tmin=tmin, tmax=tmax,
            picks=channels_idxs,
            baseline=baseline
            )
    except Exception as ex:
        return ex

    return {"instance":epochs,"events":events}

def events(**kwargs):
    input=kwargs["input"]
    params=kwargs["params"]

    events_formatted=[]
    event_formatted=[]
    t=0
    sfreq=input.info["sfreq"]
    sample=0
    if 'new_events' not in params:
        new_events=None
    else:
        new_events=params['new_events']
        if (not new_events) or (new_events == ''):
            new_events=None
        else:
            try:
                for new_event in new_events:
                    event_formatted=[]
                    new_event=new_event.split(',')

                    # sample
                    t=new_event[1]
                    sample=round(float(t)*sfreq) # time * sfreq= n_sample
                    event_formatted.append(sample)

                    # ignored
                    event_formatted.append(0)

                    # id
                    event_formatted.append(int(new_event[0]))

                    events_formatted.append(event_formatted)
                
                new_events=events_formatted
            except:
                return Response('An invalid events has been provided.',
                    status=status.HTTP_400_BAD_REQUEST)

    if new_events is not None:
        try:
            output=add_events(
                instance=input,
                new_events=new_events
                )

        except Exception as ex:
            return Response('Invalid events for add events method.',
                        status=status.HTTP_406_NOT_ACCEPTABLE)
    else:
        output=input

    return output

def peak_step(**kwargs):
    input=kwargs["input"] #objeto raw
    params=kwargs["params"]

    #SELECT CHANNELS
    #get requested channels
    channels=get_request_channels(params)
    if type(channels)==Response:
        return channels

    fields=["thresh"]
    defaults=[None]
    peak_params=check_params(params,params_names=fields,params_values=defaults)
    if type(peak_params)==Response: return peak_params

    if peak_params["thresh"] is not None:
        peak_params["thresh"]=float(peak_params["thresh"])*pow(10,-6)

    try:
        peaks=peak_finder(
            instance=input,
            channels=channels,
            thresh=peak_params["thresh"]
            )

    except Exception as ex:
        return Response('Invalid data for peak finder method',
                    status=status.HTTP_406_NOT_ACCEPTABLE)


    return {"instance":input,"method_result":peaks}

def time_series_step(**kwargs):
    params=kwargs["params"]
    if LOAD_RESTORE_PARAM_NAME not in params: # Return if not fileid for processing
            return Response('ID parameter is missing.',
                            status=status.HTTP_400_BAD_REQUEST)

    id=params[LOAD_RESTORE_PARAM_NAME]

    file_info=get_file_info(id) # Get file info from db
    if type(file_info).__name__=='Response':
        return file_info

    try:
        tu = get_upload(file_info.upload_id) # Get file from db
    except FileNotFoundError:
        return Response('Not found', status=status.HTTP_404_NOT_FOUND)

    try:
        filepath=os.path.join(tu.upload_id,tu.upload_name)
        instance=get_raw(MEDIA_TEMP,filepath)
    except Exception as ex:
        return Response('Invalid file extension',
                    status=status.HTTP_406_NOT_ACCEPTABLE)

    return instance

def result_step(**kwargs):
    return Response({
            'process_status':'SUCCESFULL',
            'result':kwargs["step_type"],
            'output_id':kwargs["step_id"]

        })

def filter_step(**kwargs):
    input=kwargs["input"]
    params=kwargs["params"]
    step_type=kwargs["step_type"]

    #SELECT FREQ
    if step_type=='BETA':
        low_freq=13.0
        high_freq=30.0

    elif step_type=='ALPHA':
        low_freq=8.0
        high_freq=13.0

    elif step_type=='THETA':
        low_freq=4.0
        high_freq=8.0

    elif step_type=='DELTA':
        low_freq=0.2
        high_freq=4.0

    elif step_type=='NOTCH':
        if 'notch_freqs' not in params:
            notch_freqs=[50.0]
        else:
            notch_freqs=params["notch_freqs"]
            if type(notch_freqs)==str:
                if (not notch_freqs) or (notch_freqs == ''):    # Si no envian nada, lo aplico en todos los canales
                    notch_freqs=[50.0]
                else:
                    try:
                        notch_freqs=[float(f) for f in notch_freqs.split(',')]
                    except:
                        return Response('An invalid list of notch frequencies has been provided.',
                            status=status.HTTP_400_BAD_REQUEST)
            elif type(notch_freqs)==list:
                if len(notch_freqs)==0:
                    return Response('An invalid list of notch frequencies has been provided.',
                        status=status.HTTP_400_BAD_REQUEST)
                else:
                    notch_freqs=[float(f) for f in notch_freqs]
    
    elif step_type=='CUSTOM_FILTER':
        if 'l_freq' not in params:
            low_freq=None
        else:
            low_freq=params['l_freq']
            if (not low_freq) or (low_freq == ''):
                low_freq=None
            else:
                try:
                    low_freq=float(low_freq)
                except:
                    return Response('An invalid low cutoff frequency has been provided.',
                        status=status.HTTP_400_BAD_REQUEST)

        if 'h_freq' not in params:
            high_freq=None
        else:
            high_freq=params['h_freq']
            if (not high_freq) or (high_freq == ''): 
                high_freq=None
            else:
                try:
                    high_freq=float(high_freq)
                except:
                    return Response('An invalid high cutoff frequency has been provided.',
                        status=status.HTTP_400_BAD_REQUEST)
 
    #SELECT CHANNELS
    #get requested channels
    channels=get_request_channels(params)
    if type(channels)==Response:
        return channels    

    if 'type' not in params:
        filter_method='fir'
    else:
        filter_method=params['type']
        if (not filter_method) or (filter_method == ''):    # Por defecto uso fir
            filter_method='fir'
        else:
            if filter_method not in ["fir","iir","spectrum_fit"]:
                return Response('An invalid type of filter has been provided.',
                    status=status.HTTP_400_BAD_REQUEST)

    # PROCESS
    if step_type=='NOTCH':
        if filter_method=='spectrum_fit':
            fields=["notch_widths","mt_bandwidth","p_value"]
            defaults=[None,None,None]
            sf_params=check_params(params,params_names=fields,params_values=defaults)
            if type(sf_params)==Response: return sf_params

            if sf_params["mt_bandwidth"] is not None:
                sf_params["mt_bandwidth"]=float(sf_params["mt_bandwidth"])
            if sf_params["p_value"] is not None:
                sf_params["p_value"]=float(sf_params["p_value"])
            
            try:
                output=notch_filter(
                    instance=input,
                    notch_freqs=notch_freqs,
                    channels=channels,
                    filter_method=filter_method,
                    notch_widths=sf_params["notch_widths"], 
                    mt_bandwidth=sf_params["mt_bandwidth"],
                    p_value=sf_params["p_value"],
                    )

            except Exception as ex:
                return Response('Invalid data for Spectrum fit filter method',
                            status=status.HTTP_406_NOT_ACCEPTABLE)

        elif filter_method=='fir':
            fields=["notch_widths","trans_bandwidth","phase","fir_window","fir_design"] #TODO: Add "pad" param
            defaults=[None,None,"zero","hamming","firwin"]
            fir_params=check_params(params,params_names=fields,params_values=defaults)
            if type(fir_params)==Response: return fir_params
            if fir_params["trans_bandwidth"] is not None:
                fir_params["trans_bandwidth"]=float(fir_params["trans_bandwidth"])

            try:
                output=notch_filter(
                    instance=input,
                    notch_freqs=notch_freqs,
                    channels=channels,
                    filter_method=filter_method,
                    notch_widths=fir_params["notch_widths"], 
                    trans_bandwidth=fir_params["trans_bandwidth"],
                    phase=fir_params["phase"],
                    fir_window=fir_params["fir_window"],
                    fir_design=fir_params["fir_design"],
                    )

            except Exception as ex:
                return Response('Invalid data for FIR filter',
                            status=status.HTTP_406_NOT_ACCEPTABLE)

        else:
            fields=["notch_widths","iir_params"]
            defaults=[None,None]
            iir_params=check_params(params,params_names=fields,params_values=defaults)
            if type(iir_params)==Response: return iir_params
            try:
                output=notch_filter(
                    instance=input,
                    notch_freqs=notch_freqs,
                    channels=channels,
                    filter_method=filter_method,
                    iir_params=iir_params["iir_params"],
                    notch_widths=iir_params["notch_widths"], 
                    )

            except Exception as ex:
                return Response('Invalid data for IIR filter',
                            status=status.HTTP_406_NOT_ACCEPTABLE)
    
    else:
        if filter_method=='fir':
            fields=["l_trans_bandwidth","h_trans_bandwidth","phase","fir_window","fir_design"] #TODO: Add "pad" param
            # defaults:
            # l_trans_bandwidth: auto = min(max(l_freq * 0.25, 2), l_freq)
            # h_trans_bandwidth: auto = min(max(h_freq * 0.25, 2.), info['sfreq'] / 2. - h_freq)
            defaults=["auto","auto","zero","hamming","firwin"]
            fir_params=check_params(params,params_names=fields,params_values=defaults)
            if fir_params["l_trans_bandwidth"]!='auto':
                fir_params["l_trans_bandwidth"]=float(fir_params["l_trans_bandwidth"])
            if fir_params["h_trans_bandwidth"]!='auto':
                fir_params["h_trans_bandwidth"]=float(fir_params["h_trans_bandwidth"])

            if type(fir_params)==Response: return fir_params
            try:
                output=custom_filter(
                    instance=input,
                    low_freq=low_freq,
                    high_freq=high_freq,
                    channels=channels,
                    filter_method=filter_method,
                    l_trans_bandwidth=fir_params["l_trans_bandwidth"], 
                    h_trans_bandwidth=fir_params["h_trans_bandwidth"],
                    phase=fir_params["phase"],
                    fir_window=fir_params["fir_window"],
                    fir_design=fir_params["fir_design"],
                    )

            except Exception as ex:
                return Response('Invalid data for FIR filter',
                            status=status.HTTP_406_NOT_ACCEPTABLE)

        else:
            fields=["iir_params"]
            defaults=[None]
            iir_params=check_params(params,params_names=fields,params_values=defaults)
            if type(iir_params)==Response: return iir_params
            try:
                output=custom_filter(
                    instance=input,
                    low_freq=low_freq,
                    high_freq=high_freq,
                    channels=channels,
                    filter_method=filter_method,
                    iir_params=iir_params["iir_params"]
                    )

            except Exception as ex:
                return Response('Invalid data for IIR filter',
                            status=status.HTTP_406_NOT_ACCEPTABLE)

    return output


steps={
    'TIME_SERIES': time_series_step,
    'PLOT_TIME_SERIES':result_step,
    'PLOT_PSD':result_step,
    'PLOT_TIME_FREQUENCY':result_step,
    'BETA':filter_step,
    'ALPHA':filter_step,
    'DELTA':filter_step,
    'THETA':filter_step,
    'NOTCH':filter_step,
    'CUSTOM_FILTER':filter_step,
    'MAX_PEAK':peak_step,
    'EVENTS': events,
    'EPOCHS':epochs,
    "SET_REFERENCE":set_reference,
    "BAD_CHANNELS":bad_channels
}