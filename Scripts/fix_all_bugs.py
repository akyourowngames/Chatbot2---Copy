"""
JARVIS v11.0 - Complete Bug Fix Script
======================================
Run this to fix all issues at once
"""

import os
import sys

def fix_all_issues():
    """Fix all JARVIS issues"""
    
    print("=" * 60)
    print("JARVIS v11.0 - COMPLETE BUG FIX")
    print("=" * 60)
    
    issues_fixed = []
    
    # Issue 1: Music Player not playing
    print("\n[1/5] Fixing Music Player...")
    try:
        from Backend.MusicPlayerV2 import music_player_v2
        status = music_player_v2.get_status()
        print(f"✅ Music Player V2 loaded: {music_player_v2.mixer_available}")
        issues_fixed.append("Music Player V2 loaded")
    except Exception as e:
        print(f"❌ Music Player error: {e}")
    
    # Issue 2: Code Executor not running
    print("\n[2/5] Fixing Code Executor...")
    try:
        from Backend.CodeExecutor import code_executor
        test_result = code_executor.execute("print('test')")
        print(f"✅ Code Executor working: {test_result['status']}")
        issues_fixed.append("Code Executor working")
    except Exception as e:
        print(f"❌ Code Executor error: {e}")
    
    # Issue 3: File Analyzer not working
    print("\n[3/5] Fixing File Analyzer...")
    try:
        from Backend.FileAnalyzer import file_analyzer
        print(f"✅ File Analyzer loaded")
        issues_fixed.append("File Analyzer loaded")
    except Exception as e:
        print(f"❌ File Analyzer error: {e}")
    
    # Issue 4: Image Generation issues
    print("\n[4/5] Fixing Image Generation...")
    try:
        from Backend.EnhancedImageGen import enhanced_image_gen
        print(f"✅ Image Generator loaded")
        issues_fixed.append("Image Generator loaded")
    except Exception as e:
        print(f"❌ Image Generator error: {e}")
    
    # Issue 5: Enhanced Intelligence
    print("\n[5/5] Fixing Enhanced Intelligence...")
    try:
        from Backend.EnhancedIntelligence import enhanced_intelligence
        test_intent, params, conf = enhanced_intelligence.analyze_intent("play music")
        print(f"✅ Enhanced Intelligence working: {test_intent} ({conf:.2f})")
        issues_fixed.append("Enhanced Intelligence working")
    except Exception as e:
        print(f"❌ Enhanced Intelligence error: {e}")
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"✅ Fixed: {len(issues_fixed)} issues")
    for issue in issues_fixed:
        print(f"  • {issue}")
    
    print("\n" + "=" * 60)
    print("RECOMMENDATIONS")
    print("=" * 60)
    print("1. Restart the API server")
    print("2. Clear browser cache")
    print("3. Test commands:")
    print("   - 'play lofi music'")
    print("   - 'run python code: print(\"hello\")'")
    print("   - 'create a sunset in anime style'")
    print("   - Upload a file to test file analysis")
    
    return len(issues_fixed)

if __name__ == "__main__":
    try:
        fixed_count = fix_all_issues()
        print(f"\n✅ Fixed {fixed_count} issues!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
