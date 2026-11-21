"""Fast-model copy of simulation/spatial-field.h (deneyler/34 DUZELTMELER.md): smooth shadow field and
position-following RMa LOS state. Network34 = hizli_model.Network with these two switched on."""
from pathlib import Path
import sys

import numpy as np
from scipy.special import erf

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent/'31_hizli_model_2026-11-20'))
import hizli_model as hm  # noqa: E402

SHADOW_SPACING, LOS_SPACING = 120.0, 60.0


def _u64(v):
    return np.asarray(v).astype(np.int64).view(np.uint64)


def node_value(seed, salt, sx, sy, ix, iy):
    with np.errstate(over='ignore'):
        key = hm._mix(np.uint64(seed) ^ (np.uint64(salt)*np.uint64(0x632be59bd9b4e019)))
        key = np.broadcast_to(key, np.broadcast(sx, sy, ix, iy).shape).copy()
        for v in (sx, sy, ix, iy):
            key = hm._mix(key ^ _u64(np.broadcast_to(v, key.shape)))
    u1 = ((hm._mix(key) >> np.uint64(11)).astype(np.float64) + 0.5)/9007199254740992.0
    u2 = ((hm._mix(key ^ np.uint64(0xa0761d6478bd642f)) >> np.uint64(11)).astype(np.float64) + 0.5)/9007199254740992.0
    return np.sqrt(-2*np.log(u1))*np.cos(2*np.pi*u2)


def field(seed, salt, ex, ey, x, y, spacing):
    """N(0,1) field value; ex, ey site position, x, y UE position (broadcastable arrays)."""
    sx, sy = hm._llround(np.asarray(ex)*1e3), hm._llround(np.asarray(ey)*1e3)
    gx, gy = np.asarray(x)/spacing, np.asarray(y)/spacing
    ix, iy = np.floor(gx).astype(np.int64), np.floor(gy).astype(np.int64)
    fx, fy = gx - ix, gy - iy
    w = [(1 - fx)*(1 - fy), fx*(1 - fy), (1 - fx)*fy, fx*fy]
    g = [node_value(seed, salt, sx, sy, ix, iy), node_value(seed, salt, sx, sy, ix + 1, iy),
         node_value(seed, salt, sx, sy, ix, iy + 1), node_value(seed, salt, sx, sy, ix + 1, iy + 1)]
    num = sum(a*b for a, b in zip(w, g))
    den = np.sqrt(sum(a*a for a in w))
    return num/den


class Network34(hm.Network):
    """Same as hizli_model.Network; shadow from the smooth field, LOS from the position field."""

    def __init__(self, sectors, ues, shadow_seed, shadow_sigma=8.0):
        super().__init__(sectors, ues, shadow_seed, shadow_sigma)
        enb = self.cells[['x_m', 'y_m', 'z_m']].to_numpy(float)
        ue = self.ues[['x_m', 'y_m', 'z_m']].to_numpy(float)
        old = hm.link_shadow(enb, ue, shadow_sigma, shadow_seed)
        ex, ey = enb[None, :, 0], enb[None, :, 1]
        ux, uy = ue[:, None, 0], ue[:, None, 1]
        new = shadow_sigma*field(shadow_seed, 1, ex, ey, ux, uy, SHADOW_SPACING)
        self.fixed_db = self.fixed_db - old + new
        u = 0.5*(1 + erf(field(shadow_seed, 2, ex, ey, ux, uy, LOS_SPACING)/np.sqrt(2)))
        self.los_fixed = u < self.p_los

    def draw_los(self, rng=None):
        return self.los_fixed
