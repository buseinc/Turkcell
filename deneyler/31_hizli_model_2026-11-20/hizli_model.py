"""Fast snapshot model of the deneyler/29 ns-3 LTE scenario: same radio formulas, no packets, no time.

Same as ns-3 (copied formula by formula from the files named):
- Path loss: 3GPP TR 38.901 RMa as in ns-3.44 three-gpp-propagation-loss-model.cc (h = 5 m, W = 20 m,
  hBS = 30 m, hUT = 1.5 m, f = DL carrier of EARFCN 1651 = 1850.1 MHz, NLOS = max(LOS, NLOS formula),
  no shadowing / O2I inside RMa). LOS/NLOS per link drawn with the ns-3 RMa probability
  exp(-(d2D - 10)/1000); ns-3 draws it from its own random stream, so single links cannot be matched,
  only the distribution.
- Antenna: 15 dBi isotropic element + 3GPP TR 36.814 pattern, A = min(A_H + A_V, 25), A_V cap 20 dB,
  tilt 6 deg, 65 / 10 deg beamwidths (deneyler/29 simulation/building-vertical-model.h).
- Link shadow: the same coordinate hash as building-vertical-model.h, sigma 8 dB, seed = shadow seed,
  so every link gets exactly the ns-3 shadow value. Per-UE extra_loss_db (distance correction).
- RSRP = 49 dBm spread over 100 RB (per 15 kHz RE) + gains - losses. Noise -174 dBm/Hz + NF 9 dB.
- SINR as ns-3 reports it with UsePdschForCqiGeneration: mean over the 100 RBs of the linear
  S / (N + EVM^2 S + interference of the neighbour cells that transmit data on that RB). A neighbour
  cell transmits on an RB with probability equal to its PRB use (random, independent RBs).

Approximations (ns-3 does these packet by packet):
- CQI from SINR with the usual 10 % BLER thresholds (CQI_DB below) instead of ns-3's MI error model;
  MCS from CQI and TB sizes are ns-3's own tables (ns3_lte_tablolari.json).
- Cell PRB use = sum over its users of (RBs per packet x packets per second) / (100 RB x 1000 TTI),
  RBs per packet = smallest number of 4-RB groups whose TB holds the packet plus headers plus the 8 B
  margin of the deneyler/29 buffer-aware PF scheduler, times 1.1 for HARQ retransmissions (10 % BLER).
- PRB use and SINR depend on each other; solved by fixed-point iteration.
"""
from pathlib import Path
import json

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
TAB = json.loads((HERE/'ns3_lte_tablolari.json').read_text())
C = 299792458.0
F_HZ = (1805.0 + 0.1*(1651 - 1200))*1e6
H_BS, H_UT, H_STREET, W_STREET = 30.0, 1.5, 5.0, 20.0
P_ENB_DBM, G_ENB_DBI, NF_DB, EVM = 49.0, 15.0, 9.0, 0.08
N_RB, RBG = 100, 4
TILT, H_BW, V_BW, AM, SLAV = 6.0, 65.0, 10.0, 25.0, 20.0
RS_DBM = P_ENB_DBM - 10*np.log10(N_RB*180e3/15e3)     # power per 15 kHz resource element
NOISE_MW = 10**((-174.0 + NF_DB + 10*np.log10(15e3))/10)
CQI_DB = np.array([-6.7, -4.7, -2.3, 0.2, 2.4, 4.3, 5.9, 8.1, 10.3, 11.7, 14.1, 16.3, 18.7, 21.0, 22.7])
HEADER_B = 12 + 8 + 20 + 2 + 2      # SeqTs + UDP + IPv4 + PDCP + RLC
PF_MARGIN_B = 8
HARQ = 1.1

M64 = np.uint64(0xFFFFFFFFFFFFFFFF)


def _mix(x):
    with np.errstate(over='ignore'):
        x = x + np.uint64(0x9e3779b97f4a7c15)
        x = (x ^ (x >> np.uint64(30)))*np.uint64(0xbf58476d1ce4e5b9)
        x = (x ^ (x >> np.uint64(27)))*np.uint64(0x94d049bb133111eb)
        return x ^ (x >> np.uint64(31))


def _llround(v):
    return (np.sign(v)*np.floor(np.abs(v) + 0.5)).astype(np.int64)


def link_shadow(enb, ue, sigma, seed):
    """ns-3 BuildingVerticalLoss::Shadow for every (UE, cell) pair; enb (C,3), ue (U,3) in metres."""
    a = _llround(np.broadcast_to(enb[None, :, :]*1e6, (len(ue), len(enb), 3)))
    b = _llround(np.broadcast_to(ue[:, None, :]*1e6, (len(ue), len(enb), 3)))
    # if (y < x) swap: lexicographic comparison of the signed integer triples
    less = (b[..., 0] < a[..., 0]) | ((b[..., 0] == a[..., 0]) & ((b[..., 1] < a[..., 1]) |
                                                                  ((b[..., 1] == a[..., 1]) & (b[..., 2] < a[..., 2]))))
    x = np.where(less[..., None], b, a).view(np.uint64)
    y = np.where(less[..., None], a, b).view(np.uint64)
    key = np.full(less.shape, _mix(np.uint64(seed)), dtype=np.uint64)
    for k in range(3):
        key = _mix(key ^ x[..., k])
    for k in range(3):
        key = _mix(key ^ y[..., k])
    u1 = ((_mix(key) >> np.uint64(11)).astype(np.float64) + 0.5)/9007199254740992.0
    u2 = ((_mix(key ^ np.uint64(0xa0761d6478bd642f)) >> np.uint64(11)).astype(np.float64) + 0.5)/9007199254740992.0
    return sigma*np.sqrt(-2*np.log(u1))*np.cos(2*np.pi*u2)


def rma_loss(d2, d3):
    """(LOS, NLOS) path loss in dB, ns-3.44 ThreeGppRmaPropagationLossModel with ranges not enforced."""
    fg = F_HZ/1e9
    dbp = 2*np.pi*H_BS*H_UT*F_HZ/C

    def pl1(d):
        return (20*np.log10(40*np.pi*d*fg/3) + min(0.03*H_STREET**1.72, 10.0)*np.log10(d)
                - min(0.044*H_STREET**1.72, 14.77) + 0.002*np.log10(H_STREET)*d)
    los = np.where(d2 <= dbp, pl1(d3), pl1(dbp) + 40*np.log10(d3/dbp))
    nlos = (161.04 - 7.1*np.log10(W_STREET) + 7.5*np.log10(H_STREET)
            - (24.37 - 3.7*(H_STREET/H_BS)**2)*np.log10(H_BS)
            + (43.42 - 3.1*np.log10(H_BS))*(np.log10(d3) - 3.0) + 20*np.log10(fg)
            - (3.2*np.log10(11.75*H_UT)**2 - 4.97))
    return los, np.maximum(los, nlos)


def pattern_loss(enb, orient, ue):
    dx = ue[:, None, 0] - enb[None, :, 0]
    dy = ue[:, None, 1] - enb[None, :, 1]
    phi = np.degrees(np.arctan2(dy, dx)) - orient[None, :]
    phi = np.fmod(phi + 540.0, 360.0) - 180.0
    ah = np.minimum(12*(phi/H_BW)**2, AM)
    elev = np.degrees(np.arctan2(enb[None, :, 2] - ue[:, None, 2], np.hypot(dx, dy)))
    av = np.minimum(12*((elev - TILT)/V_BW)**2, SLAV)
    return np.minimum(ah + av, AM)


class Network:
    """Cells from an ns-3 sectors.csv (or the same columns), users from a deneyler/29-style UE file."""

    def __init__(self, sectors, ues, shadow_seed, shadow_sigma=8.0):
        self.cells = sectors.reset_index(drop=True)
        self.ues = ues.reset_index(drop=True)
        enb = self.cells[['x_m', 'y_m', 'z_m']].to_numpy(float)
        ue = self.ues[['x_m', 'y_m', 'z_m']].to_numpy(float)
        d2 = np.hypot(ue[:, None, 0] - enb[None, :, 0], ue[:, None, 1] - enb[None, :, 1])
        d3 = np.sqrt(d2**2 + (enb[None, :, 2] - ue[:, None, 2])**2)
        self.d2 = np.maximum(d2, 1e-3)
        self.los_db, self.nlos_db = rma_loss(self.d2, d3)
        extra = self.ues['extra_loss_db'].to_numpy(float) if 'extra_loss_db' in self.ues else np.zeros(len(ue))
        self.fixed_db = (RS_DBM + G_ENB_DBI - pattern_loss(enb, self.cells['orientation_ccw_from_east_deg'].to_numpy(float), ue)
                         - extra[:, None] + link_shadow(enb, ue, shadow_sigma, shadow_seed))
        self.p_los = np.where(self.d2 <= 10, 1.0, np.exp(-(self.d2 - 10)/1000))

    def rsrp(self, los):
        """RSRP (dBm) of every (UE, cell) link for a LOS mask."""
        return self.fixed_db - np.where(los, self.los_db, self.nlos_db)

    def draw_los(self, rng):
        return rng.random(self.d2.shape) < self.p_los


def sinr(rsrp_dbm, serving, load, rng=None, samples=100, packed=True):
    """ns-3-style reported SINR (linear mean over RBs) and the SINR in dB on the RBs the UE is scheduled on.

    packed=True: ns-3's PF scheduler fills RB groups from index 0 upwards (pf-ff-mac-scheduler.cc,
    'for (int i = 0; i < rbgNum; i++)'), so a cell with PRB use rho transmits on the lowest rho x 100 RBs
    and every cell's data lands on the same low RBs. packed=False: random independent RBs (first version).
    """
    p = 10**(rsrp_dbm/10)
    u = np.arange(len(p))
    s = p[u, serving]
    interf = p.copy()
    interf[u, serving] = 0.0
    x = (np.arange(samples) + 0.5)/samples                           # position of the RB in the band
    if packed:
        act = x[:, None] < load[None, :]
    else:
        act = (rng or np.random.default_rng(0)).random((samples, len(load))) < load[None, :]
    i = interf @ act.T.astype(float)                                 # UE x RB
    lin = s[:, None]/(NOISE_MW + EVM**2*s[:, None] + i)
    db = 10*np.log10(lin)
    if packed:
        own = x[None, :] < np.maximum(load[serving], RBG/N_RB)[:, None]   # the UE's data sits on these RBs
        sched = (db*own).sum(1)/own.sum(1)
    else:
        sched = db.mean(1)
    return 10*np.log10(lin.mean(1)), sched


def mcs_from_sinr_db(x):
    cqi = np.searchsorted(CQI_DB, x, side='right')                  # 0..15
    se_cqi = np.array(TAB['SpectralEfficiencyForCqi'])
    se_mcs = np.array(TAB['SpectralEfficiencyForMcs'])
    mcs = np.array([int(np.sum(se_mcs[1:29] <= se_cqi[c])) for c in range(16)])
    return mcs[cqi], cqi


_TBS = np.array(TAB['TransportBlockSizeTable'])                    # [nprb-1][itbs]
_ITBS = np.array(TAB['McsToItbsDl'], dtype=int)


def rb_per_packet(mcs, cqi, packet_b):
    """RBs a packet occupies (all TTIs together), deneyler/29 buffer-aware PF with 4-RB groups."""
    need = (packet_b + HEADER_B + PF_MARGIN_B)*8
    tbs = _TBS[:, _ITBS[mcs]].T                                     # UE x nprb
    groups = tbs[:, RBG - 1::RBG]                                   # UE x 25 (4, 8, ..., 100 RB)
    full = groups[:, -1]
    rest = need - (np.ceil(need/full) - 1)*full                     # bits left for the last TTI
    last = np.argmax(groups >= rest[:, None], axis=1) + 1
    rb = ((np.ceil(need/full) - 1)*N_RB + last*RBG).astype(float)
    return np.where(cqi == 0, np.nan, rb*HARQ)                      # CQI 0: cannot be scheduled


def solve(net, los, packet_b, interval_ms, cell_on=None, iters=60, rng=None, samples=64):
    """Serving cell (best RSRP among cells that are on), PRB use per cell and SINR per UE."""
    rng = rng or np.random.default_rng(0)
    r = net.rsrp(los)
    on = np.ones(len(net.cells), bool) if cell_on is None else np.asarray(cell_on, bool)
    r = np.where(on[None, :], r, -np.inf)
    serving = np.argmax(r, axis=1)
    pps = 1000.0/np.asarray(interval_ms, float)
    load = np.where(on, 0.5, 0.0)
    for _ in range(iters):
        rep, cqi_db = sinr(r, serving, load)
        mcs, cqi = mcs_from_sinr_db(cqi_db)
        rb = rb_per_packet(mcs, cqi, np.asarray(packet_b, float))
        demand = np.bincount(serving, weights=np.nan_to_num(rb)*pps, minlength=len(on))/(N_RB*1000.0)
        new = np.where(on, np.minimum(demand, 1.0), 0.0)
        if np.max(np.abs(new - load)) < 1e-4:
            load = new
            break
        load = 0.5*load + 0.5*new
    rep, cqi_db = sinr(r, serving, load)
    mcs, cqi = mcs_from_sinr_db(cqi_db)
    return {'serving': serving, 'rsrp': r[np.arange(len(r)), serving], 'sinr_db': rep, 'cqi': cqi,
            'load': load, 'demand': demand, 'rb_per_packet': rb_per_packet(mcs, cqi, np.asarray(packet_b, float))}
