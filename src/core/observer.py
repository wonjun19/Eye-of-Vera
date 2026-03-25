import io
import pyautogui
from PIL import Image
from src.utils.logger import get_logger

logger = get_logger(__name__)


class Observer:
    """화면을 캡처하여 PIL Image 또는 bytes로 반환한다."""

    def capture(self) -> Image.Image:
        logger.info("화면 캡처 실행")
        screenshot = pyautogui.screenshot()
        return screenshot

    def capture_as_bytes(self) -> bytes:
        image = self.capture()
        buf = io.BytesIO()
        image.save(buf, format="PNG")
        buf.seek(0)
        return buf.read()
