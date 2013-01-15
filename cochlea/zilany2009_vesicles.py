# Description: Model of auditory periphery of: Zilany, M.S.A., Bruce,
# I.C., Nelson, P.C., and Carney, L.H. (manuscript in preparation) 2009

from __future__ import division

__author__ = "Marek Rudnicki"

import numpy as np

import _pycat
import thorns as th


class Zilany2009_Vesicles(object):
    def __init__(self, anf_num=(1,1,1), cf=1000,
                 powerlaw_implnt='approx', with_ffGn=True):
        """ Auditory periphery model of a cat (Zilany et al. 2009)

        anf_num: (hsr_num, msr_num, lsr_num)
        cf: CF
        powerlaw_implnt: 'approx' or 'actual' implementation of the power-law

        """
        self.name = 'Zilany2009'

        self._hsr_num = anf_num[0]
        self._msr_num = anf_num[1]
        self._lsr_num = anf_num[2]

        self._powerlaw_implnt = powerlaw_implnt
        self._with_ffGn = with_ffGn

        self._cohc = 1
        self._cihc = 1

        self._train_type = [('typ', 'S3'),
                            ('cf', float),
                            ('spikes', np.ndarray)]

        self.set_freq(cf)


    def run(self, fs, sound):
        """ Run the model.

        fs: sampling frequency of the signal; model is run at the same frequency
        sound: in uPa

        """
        # Run Middle Ear filter
        meout = _pycat.run_me(signal=sound, fs=fs)

        trains = []
        for cf in self._freq_map:

            # Run IHC model
            vihc = _pycat.run_ihc(signal=meout, cf=cf, fs=fs,
                                  cohc=self._cohc, cihc=self._cihc)

            # Run HSR synapse
            if self._hsr_num > 0:
                tr = self._run_anf(fs, cf, vihc,
                                   anf_type='hsr',
                                   anf_num=self._hsr_num)
                trains.extend(tr)

            # Run MSR synapse
            if self._msr_num > 0:
                tr = self._run_anf(fs, cf, vihc,
                                   anf_type='msr',
                                   anf_num=self._msr_num)
                trains.extend(tr)

            # Run LSR synapse
            if self._lsr_num > 0:
                tr = self._run_anf(fs, cf, vihc,
                                   anf_type='lsr',
                                   anf_num=self._lsr_num)
                trains.extend(tr)

        trains = np.array(trains, dtype=self._train_type)

        return trains



    def _run_anf(self, fs, cf, vihc, anf_type, anf_num):

        synout = None
        anf_trains = []
        for anf_id in range(anf_num):
            if (synout is None) or (self._with_ffGn):
                synout = _pycat.run_synapse(fs=fs, vihc=vihc, cf=cf,
                                            anf_type=anf_type,
                                            powerlaw_implnt=self._powerlaw_implnt,
                                            with_ffGn=self._with_ffGn)

            vesicles = _pycat.sample_rate(fs, synout)
            vesicles = th.signal_to_spikes(fs, vesicles)[0]

            anf_trains.append( (anf_type, cf, vesicles) )

        return anf_trains


    def set_freq(self, cf):
        """ Set signle or range of CF for the model."""
        if isinstance(cf, int):
            cf = float(cf)
        assert (isinstance(cf, tuple) or
                isinstance(cf, float))

        if isinstance(cf, float):
            self._freq_map = [cf]
        elif isinstance(cf, tuple):
            # Based on GenerateGreenwood_CFList() from DSAM
            aA = 456.0
            k = 0.8
            a = 2.1

            freq_min, freq_max, freq_num = cf

            xmin = np.log10( freq_min / aA + k) / a
            xmax = np.log10( freq_max / aA + k) / a

            x_map = np.linspace(xmin, xmax, freq_num)
            self._freq_map = aA * ( 10**( a*x_map ) - k)

    def get_freq_map(self):
        return self._freq_map



def main():
    fs = 100000
    cf = 1000
    stimdb = 30

    ear = Zilany2009_Vesicles((100,100,100), cf=cf,
                              powerlaw_implnt='approx',
                              with_ffGn=True)

    t = np.arange(0, 0.1, 1/fs)
    s = np.sin(2 * np.pi * t * cf)
    s = set_dbspl(stimdb, s)
    z = np.zeros( np.ceil(len(t)/2) )
    s = np.concatenate( (z, s, z) )

    anf = ear.run(fs, s)

    th.plot_raster(anf['spikes']).show()

    p = th.plot_psth(anf[anf['typ']=='hsr']['spikes'], color='black')
    th.plot_psth(anf[anf['typ']=='msr']['spikes'], color='red', plot=p)
    th.plot_psth(anf[anf['typ']=='lsr']['spikes'], color='blue', plot=p)
    p.show()



if __name__ == "__main__":
    main()