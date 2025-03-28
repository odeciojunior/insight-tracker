import logging
from pathlib import Path
from typing import Optional, Dict, Any, BinaryIO
import asyncio
import aiofiles
import uuid
import numpy as np
from datetime import datetime

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

class AudioProcessor:
    """Handles audio file processing and optimization."""
    
    def __init__(self, temp_dir: str = "/tmp/audio"):
        self.temp_dir = Path(temp_dir)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
    async def process_audio_file(
        self,
        file: BinaryIO,
        file_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process an uploaded audio file.
        
        Args:
            file: Audio file object
            file_id: Optional ID for the file (generated if not provided)
            
        Returns:
            Dict containing processed file information
        """
        file_id = file_id or str(uuid.uuid4())
        temp_path = self.temp_dir / f"{file_id}.wav"
        
        try:
            # Save file temporarily
            async with aiofiles.open(temp_path, 'wb') as temp_file:
                await temp_file.write(file.read())
            
            # Process audio (placeholder for actual processing)
            processing_result = await self._optimize_audio(temp_path)
            
            return {
                "file_id": file_id,
                "status": "processed",
                "duration": processing_result.get("duration", 0),
                "sample_rate": processing_result.get("sample_rate", 44100),
                "temp_path": str(temp_path),
                "processed_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing audio file {file_id}: {str(e)}")
            if temp_path.exists():
                temp_path.unlink()
            raise
    
    async def _optimize_audio(self, file_path: Path) -> Dict[str, Any]:
        """
        Optimize audio file for transcription.
        To be implemented with actual audio processing logic.
        """
        return {
            "duration": 0,
            "sample_rate": 44100,
            "channels": 1,
            "status": "optimization_pending"
        }
    
    async def cleanup_temp_files(self, max_age_hours: int = 24) -> int:
        """
        Clean up temporary audio files older than specified age.
        
        Args:
            max_age_hours: Maximum age of files in hours
            
        Returns:
            Number of files cleaned up
        """
        try:
            cleanup_count = 0
            current_time = datetime.utcnow()
            
            for file_path in self.temp_dir.glob("*.wav"):
                file_age = datetime.fromtimestamp(file_path.stat().st_mtime)
                age_hours = (current_time - file_age).total_seconds() / 3600
                
                if age_hours > max_age_hours:
                    file_path.unlink()
                    cleanup_count += 1
            
            logger.info(f"Cleaned up {cleanup_count} temporary audio files")
            return cleanup_count
            
        except Exception as e:
            logger.error(f"Error cleaning up temporary audio files: {str(e)}")
            raise

# Singleton instance
audio_processor = AudioProcessor()
