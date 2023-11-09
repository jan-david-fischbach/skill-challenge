# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/00_util.ipynb.

# %% auto 0
__all__ = ['PDK', 'nm', 'TE_pol_fraction', 'te_fraction', 'cCrossSection', 'cMode', 'inner', 'cachedComputeModes']

# %% ../nbs/00_util.ipynb 3
# util functions go here
import numpy as np
import gdsfactory.simulation.gtidy3d as gt
import matplotlib.pyplot as plt
import gdsfactory as gf
from tqdm.notebook import tqdm
import meow as mw

gf.config.rich_output()
PDK = gf.generic_tech.get_generic_pdk()
PDK.activate()

nm = 1e-3

# %% ../nbs/00_util.ipynb 5
def TE_pol_fraction(mode):
        """TE polarization fraction according to Lumericals definition. (assuming a regular mesh)"""
        Ex_sq = np.abs(mode._data["Ex"])**2
        Ey_sq = np.abs(mode._data["Ey"])**2
        
        return np.sum(Ex_sq, axis=(0,1))/np.sum(Ex_sq+Ey_sq, axis=(0,1))

from meow.mode import Mode, eps0, mu0

def te_fraction(mode: Mode) -> float:
    """the TE polarization fraction of the `Mode`"""
    epsx = np.real(mode.cs.nx**2)
    e = np.sum(0.5 * eps0 * epsx * np.abs(mode.Ex) ** 2)
    h = np.sum(0.5 * mu0 * np.abs(mode.Hx) ** 2)
    return np.real(e / (e + h))

# %% ../nbs/00_util.ipynb 6
setattr(gt.modes.Waveguide, 'TE_pol_fraction', property(TE_pol_fraction))

# %% ../nbs/00_util.ipynb 8
import meow as mw
from functools import lru_cache
import json
from hashlib import md5
from meow import BaseModel, CrossSection, Mode
from pydantic import Field

# %% ../nbs/00_util.ipynb 9
def dict_to_hash(d: dict):
  """Converts a dictionary of distinctive properties into a hash using md5"""
  arr = np.frombuffer(md5(json.dumps(d).encode()).digest(), dtype=np.uint8)[-8:]
  idx = np.arange(arr.shape[0], dtype=np.int64)[::-1]
  return np.asarray(np.sum(arr * 255**idx), dtype=np.int_).item()

# %% ../nbs/00_util.ipynb 10
class cCrossSection(BaseModel):
  cs: CrossSection = Field(
    description="the contained CrossSection"
  )

  def __hash__(self):
    m = self.cs.cell.m_full
    return dict_to_hash(dict(r=self.cs.cell.mesh.bend_radius, m=hash(m.tostring())))

  def __eq__(self, other):
    return hash(self) == hash(other)

class cMode(BaseModel):
  mode: Mode = Field(
    description="the contained Mode"
  )
  
  def getMode(self) -> Mode:
    return self.mode

  def __hash__(self):
    return dict_to_hash(dict(neff=str(self.mode.neff), r=str(self.mode.cs.cell.mesh.bend_radius)))
  
  def __eq__(self, other):
    return hash(self) == hash(other)

# %% ../nbs/00_util.ipynb 11
from functools import wraps
def cached(func):
    func.cache = {}
    @wraps(func)
    def wrapper(*args):
        try:
            return func.cache[args]
        except KeyError:
            func.cache[args] = result = func(*args)
            return result   
    return wrapper

# %% ../nbs/00_util.ipynb 12
@cached
def inner(ccs, num_modes):
  return mw.compute_modes(ccs.cs, num_modes)

def cachedComputeModes(cs, num_modes):
  modes = inner(cCrossSection(cs=cs), num_modes)
  return [mode.copy(update={'cs': cs}) for mode in modes]
