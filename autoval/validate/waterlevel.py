"""
@author: Sergey.Vinogradov@noaa.gov
"""
import os, glob
import csdllib
from csdllib.oper.sys import stampToTime, timeToStamp, msg
from datetime import datetime

#==============================================================================
def timeSeriesStats (pointFile, cfg):
    """
    Reads model time series
    Downloads/reads CO-OPS data
    Computes time series stats on a specified datespan
    """
    stats = []
    model = \
        csdllib.models.adcirc.readTimeSeries (pointFile, ncVar = 'zeta', verbose=1)
    print (model)    
    return stats
    
#==============================================================================
def waterlevel (cfg, path):
    """
    Performs waterlevel validation of a single given run.
    Returns diagnostic fields (diagFields) for multirun analysis, if requested
    """
    pointStats = []

    # Point data (time series, hardwired to COOPS tide gauges)
    if cfg['Analysis']['pointdatastats']:
        fmask = cfg['WaterLevel']['pointfilemask']
        masks = fmask.split(',')
        pointsFile = []
        for m in masks:
            f = glob.glob(path + m)
            if len(f):
                pointsFile.append(f[0])
        if len(pointsFile)>1:
            msg['w','Found more than 1 point output. Verify your mask!']
            for f in pointsFile:
                print(f)
        pointsFile = pointsFile[0]
        
        # Read list of stations
        model = \
            csdllib.models.adcirc.readTimeSeries (pointsFile, ncVar = 'zeta', verbose=1)
        stations = model['stations']
        if len(stations) == 0:
            msg('w','No stations found')
        
        # Set datespan
        dates = model['time']
        datespan = [dates[0], dates[-1]] 
        try:
            datespan[0] = stampToTime (cfg['WaterLevel'].get('pointdatesstart'))
        except:
            pass
        try:
            datespan[1] = stampToTime (cfg['WaterLevel'].get('pointdatesend'))
        except:
            pass
        msg ( 'i','Datespan for analysis is set to: ' \
            + timeToStamp(datespan[0]) + ' ' + timeToStamp(datespan[1]) )
        
        # Download / read COOPS stations data
        for n in range(len(stations)):
            forecast  = model['zeta'][:,n]
            nosid     = stations[n].strip()
            msg('i','Working on station ' + nosid)
            localFile = os.path.join(
                        cfg['Analysis']['localdatadir'], 
                        'cwl.nos.' + nosid + '.' + \
                        timeToStamp(datespan[0]) + '-' + \
                        timeToStamp(datespan[1]) + '.dat')    
            
            if not os.path.exists(localFile):
                obs = csdllib.data.coops.getData(nosid, datespan)
                csdllib.data.coops.writeData (obs, localFile)
            else:
                obs = csdllib.data.coops.readData(localFile)
            if len(obs['values']) == 0:
                msg('w','No obs found for station ' + nosid + ', skipping.')
            else:
                # Perform analysis 
                refDates, obsVals, modVals = \
                    csdllib.methods.interp.retime  (    \
                        obs['dates'], obs['values'],        \
                        model['time'], forecast, refStepMinutes=6)
                
                metrics = csdllib.methods.statistics.metrics (\
                    obsVals, modVals, refDates)
                print (metrics)

    return pointStats