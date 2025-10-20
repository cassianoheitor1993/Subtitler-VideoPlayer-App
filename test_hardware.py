#!/usr/bin/env python3
"""
Test script for Hardware Resource Manager
Shows detected hardware and optimal settings
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from resource_manager import get_resource_manager

def main():
    print("\n" + "="*70)
    print("HARDWARE RESOURCE DETECTION TEST")
    print("="*70)
    
    # Initialize resource manager
    rm = get_resource_manager()
    resources = rm.resources
    
    # Display CPU info
    print(f"\n📊 CPU:")
    print(f"   Cores: {resources.cpu_count_physical} physical, {resources.cpu_count_logical} logical")
    print(f"   Frequency: {resources.cpu_freq_max:.0f} MHz")
    print(f"   Optimal Workers: {resources.optimal_workers}")
    
    # Display RAM info
    print(f"\n💾 RAM:")
    print(f"   Total: {resources.ram_total} MB ({resources.ram_total / 1024:.1f} GB)")
    print(f"   Available: {resources.ram_available} MB ({resources.ram_available / 1024:.1f} GB)")
    print(f"   Used: {resources.ram_percent_used:.1f}%")
    
    # Display Storage info
    print(f"\n💿 Storage:")
    print(f"   Type: {resources.storage_type}")
    print(f"   SSD Detected: {'Yes ✓' if resources.has_ssd else 'No'}")
    
    # Display GPU info
    print(f"\n🎮 GPU:")
    if resources.gpu.available:
        print(f"   Name: {resources.gpu.name}")
        print(f"   Backend: {resources.gpu.backend.upper()}")
        print(f"   Memory: {resources.gpu.memory_total} MB ({resources.gpu.memory_total / 1024:.1f} GB)")
        print(f"   Available: {resources.gpu.memory_available} MB ({resources.gpu.memory_available / 1024:.1f} GB)")
        if resources.gpu.compute_capability:
            print(f"   Compute Capability: {resources.gpu.compute_capability[0]}.{resources.gpu.compute_capability[1]}")
        print(f"   FP16 Support: {'Yes ✓' if resources.use_fp16 else 'No'}")
    else:
        print(f"   Status: Not detected")
    
    # Display optimal settings
    print(f"\n⚙️  OPTIMAL SETTINGS:")
    print(f"   Use GPU: {'Yes ✓' if resources.use_gpu else 'No (CPU mode)'}")
    print(f"   Use FP16: {'Yes ✓ (2x faster!)' if resources.use_fp16 else 'No'}")
    print(f"   Optimal Batch Size: {resources.optimal_batch_size}")
    
    # Whisper config
    print(f"\n🤖 Whisper AI Configuration:")
    whisper_config = rm.get_whisper_config()
    print(f"   Device: {whisper_config['device']}")
    print(f"   FP16: {whisper_config['fp16']}")
    print(f"   Compute Type: {whisper_config['compute_type']}")
    print(f"   Beam Size: {whisper_config['beam_size']}")
    print(f"   Best Of: {whisper_config['best_of']}")
    print(f"   Recommended Model: {rm.get_recommended_model_size()}")
    
    # Translation config
    print(f"\n🌍 Translation Configuration:")
    trans_config = rm.get_translation_config()
    print(f"   Batch Size: {trans_config['batch_size']}")
    print(f"   Cache Size: {trans_config['cache_size']}")
    print(f"   Workers: {trans_config['workers']}")
    print(f"   Rate Limit: {trans_config['rate_limit_delay']}s")
    
    # FFmpeg config
    print(f"\n🎬 FFmpeg Casting Configuration:")
    ffmpeg_config = rm.get_ffmpeg_config()
    print(f"   Video Codec: {ffmpeg_config.get('video_codec', 'libx264')}")
    print(f"   Hardware Accel: {ffmpeg_config.get('hwaccel', 'none')}")
    print(f"   Preset: {ffmpeg_config.get('preset', 'medium')}")
    print(f"   Threads: {ffmpeg_config['threads']}")
    print(f"   Buffer Size: {ffmpeg_config.get('buffer_size', '4M')}")
    
    # Performance estimate
    print(f"\n📈 ESTIMATED PERFORMANCE:")
    if resources.use_gpu and resources.use_fp16:
        print(f"   AI Subtitle Generation: 5-10s per minute of video ⚡")
        print(f"   Translation (1000 subs): 20-30 seconds ⚡")
        print(f"   Casting Encode: Hardware accelerated (10x faster) ⚡")
    elif resources.use_gpu:
        print(f"   AI Subtitle Generation: 10-20s per minute of video")
        print(f"   Translation (1000 subs): 30-60 seconds")
        print(f"   Casting Encode: Hardware accelerated (5x faster)")
    else:
        print(f"   AI Subtitle Generation: 60-180s per minute of video (CPU)")
        print(f"   Translation (1000 subs): 60-120 seconds")
        print(f"   Casting Encode: Software encoding")
    
    print("\n" + "="*70)
    print("✓ Hardware detection complete!")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
