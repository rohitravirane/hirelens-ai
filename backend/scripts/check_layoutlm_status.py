"""
Check LayoutLMv3 initialization and availability status
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import structlog
from app.resumes.layout_parser.layoutlm_processor import LayoutLMProcessor

logger = structlog.get_logger()

def check_layoutlm_status():
    """Check LayoutLMv3 status"""
    print("\n" + "="*80)
    print("LAYOUTLMV3 STATUS CHECK")
    print("="*80 + "\n")
    
    try:
        print("Initializing LayoutLMProcessor...")
        processor = LayoutLMProcessor()
        
        print(f"\n✅ LayoutLMv3 Initialization Complete")
        print(f"   - Available: {processor.is_available}")
        print(f"   - Processor Loaded: {processor.processor is not None}")
        print(f"   - Model Loaded: {processor.model is not None}")
        print(f"   - Device: {processor.device}")
        
        if processor.processor:
            print(f"   - Processor Type: {type(processor.processor).__name__}")
        if processor.model:
            print(f"   - Model Type: {type(processor.model).__name__}")
        
        if not processor.is_available:
            print("\n❌ LayoutLMv3 is NOT available!")
            print("   This means vision-first parsing will use text-based fallback.")
            print("   Check logs above for initialization errors.")
        else:
            print("\n✅ LayoutLMv3 is available and ready!")
            print("   Vision-first parsing will use LayoutLMv3 for layout understanding.")
        
        print("\n" + "="*80 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error checking LayoutLMv3 status: {e}")
        import traceback
        traceback.print_exc()
        print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    check_layoutlm_status()

