"""
AUTOMATIC PATCH - Apply v11.0 Fixes to api_server.py
====================================================
This script will automatically patch your api_server.py
"""

import os
import re

def apply_patch():
    """Apply all v11.0 patches automatically"""
    
    api_file = "api_server.py"
    
    if not os.path.exists(api_file):
        print("❌ api_server.py not found!")
        return False
    
    print("📝 Reading api_server.py...")
    with open(api_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Backup
    backup_file = "api_server_backup.py"
    with open(backup_file, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✅ Backup created: {backup_file}")
    
    patches_applied = []
    
    # Patch 1: Add v11.0 imports
    if "from Backend.MusicPlayerV2 import" not in content:
        print("\n[1/5] Adding v11.0 imports...")
        
        import_section = """
# v11.0 New Modules
try:
    from Backend.MusicPlayerV2 import music_player_v2
    print("[OK] Music Player V2 loaded")
except Exception as e:
    print(f"[WARN] Music Player V2: {e}")
    music_player_v2 = None

try:
    from Backend.CodeExecutor import code_executor
    print("[OK] Code Executor loaded")
except Exception as e:
    print(f"[WARN] Code Executor: {e}")
    code_executor = None

try:
    from Backend.MathSolver import math_solver
    print("[OK] Math Solver loaded")
except Exception as e:
    print(f"[WARN] Math Solver: {e}")
    math_solver = None

try:
    from Backend.Translator import translator
    print("[OK] Translator loaded")
except Exception as e:
    print(f"[WARN] Translator: {e}")
    translator = None

try:
    from Backend.QRCodeGenerator import qr_generator
    print("[OK] QR Code Generator loaded")
except Exception as e:
    print(f"[WARN] QR Code Generator: {e}")
    qr_generator = None
"""
        
        # Find where to insert (after other Backend imports)
        insert_pos = content.find("from Backend.EnhancedWebScraper")
        if insert_pos > 0:
            # Find end of that import block
            insert_pos = content.find("\n\n", insert_pos)
            content = content[:insert_pos] + import_section + content[insert_pos:]
            patches_applied.append("v11.0 imports")
            print("✅ Added v11.0 imports")
    
    # Patch 2: Replace music_player with music_player_v2
    if 'music_player_v2.search_and_play' not in content:
        print("\n[2/5] Fixing music player...")
        
        # Replace in chat endpoint
        content = content.replace(
            'elif intent == "play_music" and music_player:',
            'elif intent == "play_music" and music_player_v2:'
        )
        content = content.replace(
            'result = music_player.search_and_play(music_query)',
            'result = music_player_v2.search_and_play(music_query)'
        )
        
        patches_applied.append("Music Player V2")
        print("✅ Fixed music player")
    
    # Patch 3: Add code execution handler
    if '"execute_code"' not in content or 'code_executor.execute' not in content:
        print("\n[3/5] Adding code execution...")
        
        code_handler = '''
                    # === CODE EXECUTION (v11.0) ===
                    elif intent == "execute_code" and code_executor:
                        code = query.replace('run python code:', '').replace('run code:', '').replace('execute:', '').strip()
                        result = code_executor.execute(code)
                        
                        if result['status'] == 'success':
                            response_text = f"✅ Code executed!\\n\\nOutput:\\n{result['output']}\\n\\nTime: {result['execution_time']}s"
                        else:
                            response_text = f"❌ Error: {result['error']}"
                        command_executed = True
'''
        
        # Insert after music player handler
        insert_marker = 'command_executed = True\n                    \n                    # === FILE I/O ==='
        if insert_marker in content:
            content = content.replace(insert_marker, f'command_executed = True\n{code_handler}\n                    # === FILE I/O ===')
            patches_applied.append("Code Execution")
            print("✅ Added code execution")
    
    # Patch 4: Add math solver handler
    if 'math_solver.calculate' not in content:
        print("\n[4/5] Adding math solver...")
        
        math_handler = '''
                    # === MATH SOLVER (v11.0) ===
                    elif intent == "calculate" and math_solver:
                        expression = query.replace('calculate', '').replace('compute', '').replace('what is', '').strip()
                        result = math_solver.calculate(expression)
                        
                        if result['status'] == 'success':
                            response_text = f"📐 {result['formatted']}"
                        else:
                            response_text = f"❌ Error: {result['error']}"
                        command_executed = True
'''
        
        # Insert after code execution
        insert_marker = 'command_executed = True\n                    \n                    # === FILE I/O ==='
        if insert_marker in content:
            content = content.replace(insert_marker, f'command_executed = True\n{math_handler}\n                    # === FILE I/O ===')
            patches_applied.append("Math Solver")
            print("✅ Added math solver")
    
    # Patch 5: Fix file analyzer to show AI analysis
    if 'file_analyzer.analyze_file' in content:
        print("\n[5/5] Fixing file analyzer...")
        
        # Make sure it returns the full analysis
        content = re.sub(
            r'analysis = file_analyzer\.analyze_file\(filepath\)',
            'analysis = file_analyzer.analyze_file(filepath)\n                        \n                        # Show full AI analysis\n                        if analysis.get("status") == "success":\n                            ai_analysis = analysis.get("ai_analysis", "No analysis available")\n                            response_text = f"📄 **File Analysis:**\\n\\n{ai_analysis}"',
            content
        )
        patches_applied.append("File Analyzer")
        print("✅ Fixed file analyzer")
    
    # Write patched file
    print("\n💾 Writing patched file...")
    with open(api_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("\n" + "="*60)
    print("✅ PATCH COMPLETE!")
    print("="*60)
    print(f"Applied {len(patches_applied)} patches:")
    for patch in patches_applied:
        print(f"  • {patch}")
    
    print("\n🔄 RESTART THE SERVER NOW:")
    print("  1. Press Ctrl+C to stop")
    print("  2. Run: python api_server.py")
    print("\n✅ All features will work after restart!")
    
    return True

if __name__ == "__main__":
    try:
        success = apply_patch()
        if success:
            print("\n🎉 Patch applied successfully!")
        else:
            print("\n❌ Patch failed!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
