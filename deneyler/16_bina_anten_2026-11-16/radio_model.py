"""Analytical replica of the ns-3 scenario's radio link budget, used for grid maps.

RSRP/RSRQ: same formula as deneyler/05 proxy, which matched native ns-3 to < 1e-6 dB.
SINR under load: native mixed CQI uses PDCCH signal and PDSCH interference from sectors
that transmit data in that subframe. Two analytical approximations are offered and both are
validated against native per-UE SINR (validate.py) before any map is drawn:
  'mean'  : S / (sum_j rho_j P_j + N)                 (average interference power)
  'mc'    : E_dB[ S / (sum_j B_j P_j + N) ], B_j ~ Bernoulli(rho_j)  (dB-average over on/off)
rho_j is the DL PRB occupancy of sector j measured in the native run (prb_usage.csv).
"""
import numpy as np

C = 299792458.0
F_DL = 1815e6
N_RB = 100
NOISE_W = 10 ** ((-174 + 9 - 30) / 10) * N_RB * 180000  # NF 9 dB, 18 MHz occupied


def received_power_w(points_xyz, sectors, beamwidth=120.0, exponent=3.0, power_dbm=49.0, max_gain_dbi=15.0):
    """Total received power [W] from each sector at each point, shape (points, sectors)."""
    sec = sectors[['x_m', 'y_m', 'z_m']].to_numpy(dtype=float)
    out = np.empty((len(points_xyz), len(sec)))
    orient = np.deg2rad(sectors.orientation_ccw_from_east_deg.to_numpy(dtype=float))
    shape = -3 / (20 * np.log10(np.cos(np.deg2rad(beamwidth / 4))))
    ref = 20 * np.log10(4 * np.pi * F_DL / C)
    for start in range(0, len(points_xyz), 20000):
        p = points_xyz[start:start + 20000]
        d = p[:, None, :] - sec[None, :, :]
        dist = np.linalg.norm(d, axis=2)
        ang = np.arctan2(d[:, :, 1], d[:, :, 0]) - orient[None, :]
        ang = (ang + np.pi) % (2 * np.pi) - np.pi
        gain = np.cos(ang / 2) ** (2 * shape)
        loss = ref + 10 * exponent * np.log10(np.maximum(dist, 1))
        out[start:start + 20000] = 10 ** ((power_dbm + max_gain_dbi - loss - 30) / 10) * gain
    return out


def link_metrics(pw, rho=None, method='mean', draws=400, seed=0):
    """Serving sector (strongest), RSRP, RSRQ (load-independent in this ns-3 model) and SINR."""
    n = len(pw)
    serving = pw.argmax(axis=1)
    s = pw[np.arange(n), serving]
    other = pw.sum(axis=1) - s
    out = {'serving': serving,
           'rsrp_dbm': 10 * np.log10(s / (N_RB * 12)) + 30,
           'rsrq_db': 10 * np.log10(s / (2 * (s + other + NOISE_W))),
           'snr_db': 10 * np.log10(s / NOISE_W),
           'control_sinr_db': 10 * np.log10(s / (other + NOISE_W))}
    if rho is None:
        return out
    rho = np.asarray(rho, dtype=float)
    weights = np.broadcast_to(rho, pw.shape).copy()
    weights[np.arange(n), serving] = 0.0
    if method == 'mean':
        out['sinr_db'] = 10 * np.log10(s / ((pw * weights).sum(axis=1) + NOISE_W))
    elif method == 'ns3mix':
        # Native mixed CQI uses PDSCH interference only when a fresh data-interference update
        # exists (serving sector transmitted data that subframe); otherwise noise only (S/N).
        # Fresh fraction ~ serving-sector occupancy; dB average over both kinds of samples.
        fresh = link_metrics(pw, rho, 'mc', draws, seed)['sinr_db']
        f = rho[serving]
        out['sinr_db'] = f * fresh + (1 - f) * out['snr_db']
        out['interference_sinr_db'] = fresh
    elif method == 'mc':
        rng = np.random.default_rng(seed)
        acc = np.zeros(n)
        for _ in range(draws):
            on = rng.random(pw.shape[1]) < rho
            interf = (pw * on[None, :]).sum(axis=1) - np.where(on[serving], s, 0.0)
            acc += 10 * np.log10(s / (interf + NOISE_W))
        out['sinr_db'] = acc / draws
    else:
        raise ValueError(method)
    return out
