"""
Hardware Resource Manager
Dynamically detects and allocates hardware resources for optimal performance
"""

import os
import sys
import platform
import subprocess
import psutil
from dataclasses import dataclass
from typing import Optional, Dict, List
from pathlib import Path

import logging
logger = logging.getLogger(__name__)


@dataclass
class GPUInfo:
    """Information about available GPU"""
    available: bool = False
    name: str = "None"
    memory_total: int = 0  # MB
    memory_available: int = 0  # MB
    compute_capability: Optional[tuple] = None  # (major, minor) for CUDA
    backend: str = "none"  # cuda, rocm, mps, none


@dataclass
class SystemResources:
    """Complete system resource information"""
    # CPU
    cpu_count_physical: int = 0
    cpu_count_logical: int = 0
    cpu_freq_max: float = 0.0  # MHz
    
    # RAM
    ram_total: int = 0  # MB
    ram_available: int = 0  # MB
    ram_percent_used: float = 0.0
    
    # Storage
    has_ssd: bool = False
    storage_type: str = "unknown"
    
    # GPU
    gpu: GPUInfo = None
    
    # Derived optimal settings
    optimal_workers: int = 1
    optimal_batch_size: int = 1
    use_fp16: bool = False
    use_gpu: bool = False


class ResourceManager:
    """Manages hardware resource detection and allocation"""
    
    def __init__(self):
        """Initialize resource manager and detect hardware"""
        self.resources = SystemResources()
        self.resources.gpu = GPUInfo()
        self._detect_all_resources()
        self._calculate_optimal_settings()
        self._log_system_info()
    
    def _detect_all_resources(self):
        """Detect all available hardware resources"""
        self._detect_cpu()
        self._detect_ram()
        self._detect_storage()
        self._detect_gpu()
    
    def _detect_cpu(self):
        """Detect CPU information"""
        try:
            self.resources.cpu_count_physical = psutil.cpu_count(logical=False) or 1
            self.resources.cpu_count_logical = psutil.cpu_count(logical=True) or 1
            
            # Get CPU frequency
            cpu_freq = psutil.cpu_freq()
            if cpu_freq:
                self.resources.cpu_freq_max = cpu_freq.max or cpu_freq.current or 0.0
            
            logger.info(f"CPU: {self.resources.cpu_count_physical} cores "
                       f"({self.resources.cpu_count_logical} threads) @ {self.resources.cpu_freq_max:.0f} MHz")
        except Exception as e:
            logger.warning(f"Error detecting CPU: {e}")
    
    def _detect_ram(self):
        """Detect RAM information"""
        try:
            mem = psutil.virtual_memory()
            self.resources.ram_total = mem.total // (1024 * 1024)  # Convert to MB
            self.resources.ram_available = mem.available // (1024 * 1024)
            self.resources.ram_percent_used = mem.percent
            
            logger.info(f"RAM: {self.resources.ram_total} MB total, "
                       f"{self.resources.ram_available} MB available ({mem.percent:.1f}% used)")
        except Exception as e:
            logger.warning(f"Error detecting RAM: {e}")
    
    def _detect_storage(self):
        """Detect storage type (SSD vs HDD)"""
        try:
            system = platform.system()
            
            if system == "Linux":
                # Check if root partition is on SSD
                result = subprocess.run(
                    ["lsblk", "-d", "-o", "name,rota"],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                if result.returncode == 0:
                    # rota=0 means SSD, rota=1 means HDD
                    for line in result.stdout.split('\n')[1:]:
                        if line.strip():
                            parts = line.split()
                            if len(parts) >= 2 and parts[1] == '0':
                                self.resources.has_ssd = True
                                self.resources.storage_type = "SSD"
                                break
                    if not self.resources.has_ssd:
                        self.resources.storage_type = "HDD"
            
            elif system == "Windows":
                # Windows detection via WMI
                try:
                    result = subprocess.run(
                        ["powershell", "-Command", 
                         "Get-PhysicalDisk | Select-Object MediaType"],
                        capture_output=True,
                        text=True,
                        timeout=2
                    )
                    if "SSD" in result.stdout:
                        self.resources.has_ssd = True
                        self.resources.storage_type = "SSD"
                    elif "HDD" in result.stdout:
                        self.resources.storage_type = "HDD"
                except:
                    pass
            
            elif system == "Darwin":  # macOS
                # Most modern Macs have SSD
                self.resources.has_ssd = True
                self.resources.storage_type = "SSD (assumed)"
            
            logger.info(f"Storage: {self.resources.storage_type}")
        except Exception as e:
            logger.warning(f"Error detecting storage type: {e}")
            self.resources.storage_type = "unknown"
    
    def _detect_gpu(self):
        """Detect GPU and determine best backend"""
        # Try CUDA (NVIDIA)
        if self._detect_cuda():
            return
        
        # Try ROCm (AMD)
        if self._detect_rocm():
            return
        
        # Try MPS (Apple Silicon)
        if self._detect_mps():
            return
        
        logger.info("No GPU acceleration available - using CPU")
    
    def _detect_cuda(self) -> bool:
        """Detect NVIDIA CUDA GPU"""
        try:
            import torch
            
            if torch.cuda.is_available():
                self.resources.gpu.available = True
                self.resources.gpu.backend = "cuda"
                self.resources.gpu.name = torch.cuda.get_device_name(0)
                
                # Get memory info
                props = torch.cuda.get_device_properties(0)
                self.resources.gpu.memory_total = props.total_memory // (1024 * 1024)
                self.resources.gpu.compute_capability = (props.major, props.minor)
                
                # Get available memory
                mem_free, mem_total = torch.cuda.mem_get_info(0)
                self.resources.gpu.memory_available = mem_free // (1024 * 1024)
                
                logger.info(f"GPU: {self.resources.gpu.name} (CUDA)")
                logger.info(f"GPU Memory: {self.resources.gpu.memory_total} MB total, "
                           f"{self.resources.gpu.memory_available} MB available")
                logger.info(f"Compute Capability: {self.resources.gpu.compute_capability}")
                
                return True
        except ImportError:
            logger.debug("PyTorch not available for CUDA detection")
        except Exception as e:
            logger.debug(f"CUDA detection failed: {e}")
        
        return False
    
    def _detect_rocm(self) -> bool:
        """Detect AMD ROCm GPU"""
        try:
            import torch
            
            if hasattr(torch, 'hip') and torch.hip.is_available():
                self.resources.gpu.available = True
                self.resources.gpu.backend = "rocm"
                self.resources.gpu.name = torch.hip.get_device_name(0)
                
                props = torch.hip.get_device_properties(0)
                self.resources.gpu.memory_total = props.total_memory // (1024 * 1024)
                
                logger.info(f"GPU: {self.resources.gpu.name} (ROCm)")
                logger.info(f"GPU Memory: {self.resources.gpu.memory_total} MB")
                
                return True
        except (ImportError, AttributeError):
            pass
        except Exception as e:
            logger.debug(f"ROCm detection failed: {e}")
        
        return False
    
    def _detect_mps(self) -> bool:
        """Detect Apple Metal Performance Shaders (Apple Silicon)"""
        try:
            import torch
            
            if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                self.resources.gpu.available = True
                self.resources.gpu.backend = "mps"
                self.resources.gpu.name = "Apple Silicon GPU"
                
                logger.info(f"GPU: {self.resources.gpu.name} (MPS)")
                
                return True
        except (ImportError, AttributeError):
            pass
        except Exception as e:
            logger.debug(f"MPS detection failed: {e}")
        
        return False
    
    def _calculate_optimal_settings(self):
        """Calculate optimal settings based on available resources"""
        # Determine if we can use GPU
        self.resources.use_gpu = self.resources.gpu.available
        
        # FP16 support (NVIDIA with compute capability >= 7.0, or RTX series)
        if self.resources.gpu.backend == "cuda":
            if self.resources.gpu.compute_capability:
                major, minor = self.resources.gpu.compute_capability
                # RTX cards (Turing and newer) have compute capability >= 7.5
                self.resources.use_fp16 = (major >= 7 and minor >= 5) or major >= 8
            # Also check GPU name for RTX
            if "RTX" in self.resources.gpu.name.upper():
                self.resources.use_fp16 = True
        
        # Calculate optimal worker count
        # Use physical cores - 1 for workers, keep 1 for main thread
        self.resources.optimal_workers = max(1, self.resources.cpu_count_physical - 1)
        
        # Calculate optimal batch size based on RAM and GPU
        if self.resources.gpu.available:
            # GPU-based batch size (conservative estimate: 1GB per batch of 32)
            gpu_batch = (self.resources.gpu.memory_available // 1024) * 32
            self.resources.optimal_batch_size = min(64, max(8, gpu_batch))
        else:
            # CPU-based batch size (conservative: 100MB per item)
            ram_batch = (self.resources.ram_available // 100)
            self.resources.optimal_batch_size = min(32, max(4, ram_batch))
    
    def _log_system_info(self):
        """Log complete system information"""
        logger.info("=" * 60)
        logger.info("SYSTEM RESOURCES DETECTED")
        logger.info("=" * 60)
        logger.info(f"Platform: {platform.system()} {platform.release()}")
        logger.info(f"CPU: {self.resources.cpu_count_physical} cores, "
                   f"{self.resources.cpu_count_logical} threads")
        logger.info(f"RAM: {self.resources.ram_total} MB "
                   f"({self.resources.ram_available} MB available)")
        logger.info(f"Storage: {self.resources.storage_type}")
        
        if self.resources.gpu.available:
            logger.info(f"GPU: {self.resources.gpu.name} ({self.resources.gpu.backend})")
            logger.info(f"GPU Memory: {self.resources.gpu.memory_total} MB")
            logger.info(f"FP16 Support: {'Yes' if self.resources.use_fp16 else 'No'}")
        else:
            logger.info("GPU: None detected")
        
        logger.info("-" * 60)
        logger.info("OPTIMAL SETTINGS")
        logger.info("-" * 60)
        logger.info(f"Use GPU: {self.resources.use_gpu}")
        logger.info(f"Use FP16: {self.resources.use_fp16}")
        logger.info(f"Optimal Workers: {self.resources.optimal_workers}")
        logger.info(f"Optimal Batch Size: {self.resources.optimal_batch_size}")
        logger.info("=" * 60)
    
    def get_whisper_config(self) -> Dict:
        """Get optimal configuration for Whisper AI"""
        config = {
            "device": self.resources.gpu.backend if self.resources.use_gpu else "cpu",
            "fp16": self.resources.use_fp16 and self.resources.use_gpu,
            "compute_type": "float16" if (self.resources.use_fp16 and self.resources.use_gpu) else "float32",
            # Faster decoding strategies for GPU
            "beam_size": 5 if self.resources.use_gpu else 1,
            "best_of": 5 if self.resources.use_gpu else 1,
            # Memory optimization
            "condition_on_previous_text": self.resources.use_gpu,
            "compression_ratio_threshold": 2.4,
            "no_speech_threshold": 0.6,
            # Performance
            "threads": self.resources.optimal_workers if not self.resources.use_gpu else 0,
        }
        
        return config
    
    def get_translation_config(self) -> Dict:
        """Get optimal configuration for translation"""
        # Increase batch sizes significantly with good RAM
        if self.resources.ram_available > 8000:  # > 8GB available
            batch_size = 50
            cache_size = 5000
        elif self.resources.ram_available > 4000:  # > 4GB available
            batch_size = 30
            cache_size = 3000
        else:
            batch_size = 10
            cache_size = 1000
        
        config = {
            "batch_size": batch_size,
            "cache_size": cache_size,
            "workers": min(4, self.resources.optimal_workers),  # Parallel translation workers
            "rate_limit_delay": 0.2 if self.resources.ram_available > 4000 else 0.5,
        }
        
        return config
    
    def get_ffmpeg_config(self) -> Dict:
        """Get optimal FFmpeg encoding configuration"""
        config = {
            "threads": self.resources.optimal_workers,
            "preset": "fast" if self.resources.has_ssd else "medium",
        }
        
        # Hardware encoding settings
        if self.resources.gpu.available:
            if self.resources.gpu.backend == "cuda":
                # NVIDIA NVENC
                config["hwaccel"] = "cuda"
                config["video_codec"] = "h264_nvenc"
                config["preset_nvenc"] = "p4"  # Balanced (p1=fast, p7=slow)
                config["rc"] = "vbr"  # Variable bitrate
                config["gpu"] = "0"
            elif self.resources.gpu.backend == "rocm":
                # AMD VCE
                config["hwaccel"] = "vaapi"
                config["video_codec"] = "h264_vaapi"
            elif self.resources.gpu.backend == "mps":
                # Apple VideoToolbox
                config["hwaccel"] = "videotoolbox"
                config["video_codec"] = "h264_videotoolbox"
        else:
            # Software encoding
            config["video_codec"] = "libx264"
            config["preset"] = "veryfast" if self.resources.cpu_count_physical >= 4 else "ultrafast"
        
        # Buffer size optimization
        if self.resources.has_ssd:
            config["buffer_size"] = "8M"
        else:
            config["buffer_size"] = "4M"
        
        return config
    
    def get_current_resources(self) -> SystemResources:
        """Get current resource snapshot (updated RAM)"""
        # Update dynamic values
        try:
            mem = psutil.virtual_memory()
            self.resources.ram_available = mem.available // (1024 * 1024)
            self.resources.ram_percent_used = mem.percent
            
            if self.resources.gpu.available and self.resources.gpu.backend == "cuda":
                try:
                    import torch
                    mem_free, _ = torch.cuda.mem_get_info(0)
                    self.resources.gpu.memory_available = mem_free // (1024 * 1024)
                except:
                    pass
        except Exception as e:
            logger.warning(f"Error updating resources: {e}")
        
        return self.resources
    
    def get_resource_usage_string(self) -> str:
        """Get formatted string of current resource usage"""
        self.get_current_resources()
        
        usage = []
        usage.append(f"RAM: {self.resources.ram_percent_used:.0f}%")
        
        if self.resources.gpu.available:
            gpu_used_percent = ((self.resources.gpu.memory_total - self.resources.gpu.memory_available) 
                               / self.resources.gpu.memory_total * 100)
            usage.append(f"GPU: {gpu_used_percent:.0f}%")
        
        return " | ".join(usage)
    
    def should_use_gpu_for_task(self, estimated_memory_mb: int = 2000) -> bool:
        """Check if GPU should be used for a task"""
        if not self.resources.gpu.available:
            return False
        
        # Ensure enough GPU memory is available
        self.get_current_resources()
        return self.resources.gpu.memory_available >= estimated_memory_mb
    
    def get_recommended_model_size(self) -> str:
        """Get recommended Whisper model size based on resources"""
        if not self.resources.gpu.available:
            # CPU only - use smaller models
            if self.resources.ram_available < 2000:
                return "tiny"
            elif self.resources.ram_available < 4000:
                return "base"
            else:
                return "small"
        
        # GPU available - can use larger models
        gpu_mem = self.resources.gpu.memory_available
        
        if gpu_mem >= 10000:  # 10GB+
            return "large"
        elif gpu_mem >= 5000:  # 5GB+
            return "medium"
        elif gpu_mem >= 2000:  # 2GB+
            return "small"
        else:
            return "base"


# Global instance
_resource_manager = None


def get_resource_manager() -> ResourceManager:
    """Get global resource manager instance"""
    global _resource_manager
    if _resource_manager is None:
        _resource_manager = ResourceManager()
    return _resource_manager
