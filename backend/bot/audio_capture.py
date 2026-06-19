import subprocess
import logging
import os
import signal

logger = logging.getLogger(__name__)

class AudioCapture:
    def __init__(self, output_dir="/tmp/hjai_audio"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.process = None
        
    def start_recording(self, meeting_id: str):
        output_file = os.path.join(self.output_dir, f"{meeting_id}.wav")
        logger.info(f"Starting audio capture to {output_file}")
        
        # FFmpeg command to capture from PulseAudio default sink (usually the virtual sink set up in Docker)
        # -f pulse : Format pulse audio
        # -i default : input from default device
        command = [
            "ffmpeg",
            "-y", # Overwrite output files without asking
            "-f", "pulse",
            "-i", "default",
            "-ac", "1", # Mono channel
            "-ar", "16000", # 16kHz is ideal for Whisper
            output_file
        ]
        
        try:
            # We don't want to block, so we use Popen
            self.process = subprocess.Popen(
                command,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                preexec_fn=os.setsid # So we can kill the whole process group later
            )
            logger.info(f"Audio capture started with PID {self.process.pid}")
            return output_file
        except Exception as e:
            logger.error(f"Failed to start FFmpeg: {e}")
            raise e
            
    def stop_recording(self):
        if self.process:
            logger.info("Stopping audio capture...")
            try:
                os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
                self.process.wait(timeout=5)
            except Exception as e:
                logger.error(f"Error stopping FFmpeg: {e}")
            finally:
                self.process = None
                logger.info("Audio capture stopped.")
