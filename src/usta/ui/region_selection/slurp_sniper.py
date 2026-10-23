import logging
import os
import time
from PySide6.QtCore import QRect
from PySide6.QtWidgets import QApplication
from usta.ui.region_selection.base_sniper import BaseSniper
from usta.config import SLURP_TEMP_PATH

logger = logging.getLogger(__name__)

class SlurpSniper(BaseSniper):
    def get_region(self) -> QRect | None:
        """Selects a region on the screen using slurp."""
        if os.path.exists(SLURP_TEMP_PATH):
            os.remove(SLURP_TEMP_PATH)
        
        try:
            # Run slurp and write output to file
            os.system(f"slurp -f '%x,%y %w,%h' > {SLURP_TEMP_PATH} 2>/dev/null &")
            start = time.time()
            output = ""
            while time.time() - start < 30: # 30 seconds timeout
                QApplication.processEvents()
                if os.path.exists(SLURP_TEMP_PATH) and os.path.getsize(SLURP_TEMP_PATH) > 0:
                    time.sleep(0.1)
                    with open(SLURP_TEMP_PATH, "r") as f:
                        output = f.read().strip()
                    break
                time.sleep(0.1)
            
            if output:
                p = output.split()
                if len(p) >= 2:
                    x, y = map(int, p[0].split(","))
                    w, h = map(int, p[1].split(","))
                    return QRect(x, y, w, h)
        except Exception as e:
            logger.error(f"Region Selection Error (slurp): {e}")
        finally:
            if os.path.exists(SLURP_TEMP_PATH):
                os.remove(SLURP_TEMP_PATH)
        return None
