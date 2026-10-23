from usta.core.sniper.base_sniper import BaseSniper
from usta.core.sniper.slurp_sniper import SlurpSniper
from usta.core.sniper.core_sniper import CoreSniper

class SniperFactory:
    @staticmethod
    def get_engine() -> BaseSniper:
        # Currently only Slurp (Wayland) is supported.
        # Future implementations can check OS/DE and return the appropriate engine.
        #return SlurpSniper()
        return CoreSniper()
